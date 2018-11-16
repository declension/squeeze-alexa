#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   Copyright 2018 Nick Boultbee
#   This file is part of squeeze-alexa.
#
#   squeeze-alexa is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   See LICENSE for full license

import argparse
import enum
import json
import logging
import re
import sys
from io import BytesIO
from os import path, walk, chdir
from os.path import dirname, realpath, isdir
from tarfile import TarFile, TarInfo
from typing import BinaryIO, Set, Union
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo

import boto3
from botocore.exceptions import ClientError

ROOT = dirname(dirname(realpath(__file__)))
DIST_SUBDIR = "dist"

OUTPUT_ZIP = path.join(ROOT, "lambda_function.zip")
MQTT_OUTPUT_GZIP = path.join(ROOT, "mqtt-squeeze.tgz")

LAMBDA_NAME = "squeeze-alexa"
MANAGED_POLICY_ARN = ("arn:aws:iam::aws:policy/service-role/"
                      "AWSLambdaBasicExecutionRole")
ROLE_NAME = "squeeze-alexa"
EXCLUDE_REGEXES = [re.compile(s) for s in
                   (r"__pycache__/", r"\.git/", r"^\..+",
                    r"docs/", r"metadata/",
                    r"\.po$", r"~$", r"\.pyc$", r"\\.md$", r"\.zip$")]


class Commands(enum.Enum):
    AWS_DEPLOY = 'aws'
    ZIP_MQTT = 'mqtt'
    ZIP_SKILL = 'zip'


logging.basicConfig(format="[{levelname:7s}] {message}",
                    style="{")
log = logging.getLogger("squeeze-alexa-uploader")
log.setLevel(logging.INFO)

ROLE_POLICY_DOC = json.dumps({
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "",
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
})

Arn = str


class Error(Exception):
    """Base Exception"""
    pass


def suitable(name: str) -> bool:
    for r in EXCLUDE_REGEXES:
        if r.search(name):
            return False
    return True


def main(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description="squeeze-alexa deployer")
    parser.add_argument("-v", "--verbose", help="Verbose logging",
                        action="store_true")

    subparsers = parser.add_subparsers(dest="cmd", help="Command")
    subparsers.required = True
    subparsers.add_parser(Commands.ZIP_SKILL.value, help='create local zip')

    subparsers.add_parser(Commands.ZIP_MQTT.value,
                          help='create mqtt-squeeze zip')

    aws_parser = subparsers.add_parser(Commands.AWS_DEPLOY.value,
                                       help='Set up AWS Lambda')
    aws_parser.add_argument("--profile", action="store",
                            help="AWS profile to use")
    aws_parser.add_argument("--skill", required=True, action="store",
                            metavar="SKILL_ID",
                            help="Your Alexa skill ID (amzn1.ask.skill....)")
    args = parser.parse_args(args)
    log.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    log.debug(args)

    dist_dir = path.join(ROOT, DIST_SUBDIR)
    if isdir(dist_dir):
        log.info("Using built code and config from directory: %s", dist_dir)
    else:
        dist_dir = ROOT
        log.info("No '%s/' dir found, using root %s for files",
                 DIST_SUBDIR, ROOT)
    chdir(dist_dir)
    c = Commands(args.cmd)
    if c == Commands.AWS_DEPLOY:
        log.debug("Setting up AWS Lambda")
        aws_upload(args, create_skill_zip())
    elif c == Commands.ZIP_MQTT:
        log.debug("Creating tgz for mqtt-squeeze")
        with open(MQTT_OUTPUT_GZIP, "wb") as f:
            create_mqtt_gzip(f, root=dist_dir)
        log.info("Wrote %s", MQTT_OUTPUT_GZIP)
    else:
        log.info("Creating zip for manual skill upload. "
                 "Use '%s' command to setup skill automatically",
                 Commands.AWS_DEPLOY.value)
        zipped = create_skill_zip()
        with open(OUTPUT_ZIP, "wb") as f:
            f.write(zipped.read())
        log.info("Wrote %s", OUTPUT_ZIP)


def aws_upload(args: argparse.Namespace, zip_data: BinaryIO):
    if args.profile:
        session = boto3.session.Session()
        log.debug("Available profiles: %s", session.available_profiles)
        log.info("Using profile: %s", args.profile)
        boto3.setup_default_session(profile_name=args.profile)
    role_arn = set_up_role()
    if lambda_exists():
        upload(zip_data)
    else:
        arn = create_lambda(role_arn, zip_data, args.skill)
        print("Lambda ARN:", arn)


def lambda_exists(name=LAMBDA_NAME) -> bool:
    lam = boto3.client("lambda")
    try:
        lam.get_function(FunctionName=name)
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceNotFoundException":
            raise
        return False
    else:
        log.info("AWS Lambda '%s' already exists. Updating code only...", name)
        return True


def upload(zip: BinaryIO, name=LAMBDA_NAME):
    lam = boto3.client("lambda")
    r = lam.update_function_code(FunctionName=name,
                                 ZipFile=zip.read())
    log.info("Updated Lambda: %s", r['FunctionArn'])
    log.debug("Updated %s (\"%s\"), with %.0f KB of zipped data",
              name, r["Description"], r["CodeSize"] / 1024)


def create_lambda(role_arn: str, zip_data: BinaryIO, skill_id: str) -> Arn:
    lam = boto3.client("lambda")
    resp = lam.create_function(FunctionName=LAMBDA_NAME,
                               Runtime="python3.6",
                               Handler="handler.lambda_handler",
                               Code={"ZipFile": zip_data.read()},
                               Description="Squeezebox integration for Alexa",
                               Role=role_arn,
                               Timeout=8)
    log.debug("Creation response: %s", resp)

    r = lam.add_permission(
        FunctionName=LAMBDA_NAME,
        StatementId="AlexaFunctionPermission",
        Action="lambda:InvokeFunction",
        Principal="alexa-appkit.amazon.com",
        EventSourceToken="amzn1.ask.skill.%s" % skill_id)
    log.debug("Permissioning response: %s", r)
    return resp["FunctionArn"]


def create_skill_zip() -> BinaryIO:
    def files_in(zf: ZipFile, ext: str) -> Set[ZipInfo]:
        return {f for f in zf.filelist if f.filename.endswith(ext)}
    log.debug("Compressing Skill deployment files")
    io = BytesIO()
    with ZipFile(io, "w") as zf:
        for root, dirs, fns in walk("./"):
            for d in list(dirs):
                if not suitable(d + "/"):
                    dir_path = path.join(root, d)
                    log.debug("Excluding dir: %s", dir_path)
                    try:
                        dirs.remove(d)
                    except ValueError:
                        log.warning("Couldn't remove %s", dir_path)
            for name in fns:
                if suitable(name):
                    zf.write(path.join(root, name), compress_type=ZIP_DEFLATED)
    if not files_in(zf, '.mo'):
        raise Error("Can't find any translations (.mo files). "
                    "Did you forget to run the build first?")
    log.debug("All files: %s", ", ".join(zi.filename for zi in zf.filelist))
    io.seek(0)
    log.info("Added %d files to zip (%.0f KB total)",
             len(zf.filelist), len(io.read()) / 1024)
    io.seek(0)
    return io


def create_mqtt_gzip(f: BinaryIO, root: str = ROOT) -> None:
    def exclude_bad(ti: TarInfo) -> Union[TarInfo, None]:
        for r in EXCLUDE_REGEXES:
            if r.search(ti.name):
                return None
        return ti
    log.debug("Compressing MQTT deployment files")
    with TarFile.gzopen("mqtt-squeeze", mode="w", fileobj=f) as tf:
        tf.add(path.join(ROOT, 'mqtt_squeeze.py'), arcname='mqtt_squeeze.py')
        for d in ['etc', 'squeezealexa']:
            tf.add(path.join(root, d), arcname=d, filter=exclude_bad)

        if not [fn for fn in tf.getnames() if fn.endswith('.pem.crt')]:
            raise Error("Can't find any certs (.pem.crt files). "
                        "Make sure you create these first in /etc/certs")
        log.debug("All files: %s", ", ".join(tf.getnames()))


def set_up_role() -> str:
    iam = boto3.client("iam")

    def create_role() -> dict:
        response = iam.create_role(RoleName=ROLE_NAME,
                                   AssumeRolePolicyDocument=ROLE_POLICY_DOC)
        iam.attach_role_policy(RoleName=ROLE_NAME,
                               PolicyArn=MANAGED_POLICY_ARN)
        return response

    try:
        role = create_role()
    except ClientError as e:
        if e.response["Error"]["Code"] != "EntityAlreadyExists":
            raise
        try:
            logging.info("Deleting existing role...")
            iam.delete_role(RoleName=ROLE_NAME)
        except ClientError:
            logging.info("Detaching existing role first...")
            role = boto3.resource("iam").Role(ROLE_NAME)
            role.detach_policy(PolicyArn=MANAGED_POLICY_ARN)
            role.delete()
        role = create_role()
    return role["Role"]["Arn"]


if __name__ == "__main__":
    main()
