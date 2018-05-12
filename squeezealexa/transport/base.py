# -*- coding: utf-8 -*-
#
#   Copyright 2017 Nick Boultbee
#   This file is part of squeeze-alexa.
#
#   squeeze-alexa is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   See LICENSE for full license


class Error(Exception):

    def __init__(self, msg, e):
        super(Error, self).__init__(msg)
        self.message = msg
        self.__cause__ = e


class Transport(object):
    """Communications transport
    for half-duplex / send-then-maybe-listen mode of communications"""

    def communicate(self, data, wait=True):
        """Send `data`, waiting if `wait` is True
        :param [str] data: Data to send
        :param bool wait: Block for response if True
        :rtype: str
        :return: response lines, if any"""
        raise NotImplementedError()

    @property
    def details(self):
        """:return: String of connection details"""
        raise NotImplementedError()

    def __str__(self):
        return self.details()
