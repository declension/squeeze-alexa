#!/usr/bin/env bash
set -e

includes="handler.py squeezealexa/ locale/ etc/"

root=$(readlink -f "$(dirname $0)/..")

output="$root/lambda_function.zip"
mode=$1
version=${2:-latest}
if test "$mode" == "release"; then
    echo "<<<< Doing release build for version '$version'. Continue?... >>>>"
    read -n 1 -p "Continue? (ctrl-c to abort)"

    extras="--exclude *.pem";
    $(dirname $0)/compile-translations
    echo -e "\nContinuing with build...\n"
    output="squeeze-alexa-release-$2.zip"
    includes="$includes metadata/ bin/local_test.py docs/ README.md"
fi

pushd "$root"
echo "Installing Pipenv dependencies..."
pipenv install --dev
pipenv run pipenv_to_requirements -f
dist_dir="$PWD/dist"
[ -e "$dist_dir" ] && rm -rf "$dist_dir"
mkdir "$dist_dir"
cd "$dist_dir"

# Do this the simpler way...
# See https://docs.aws.amazon.com/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html
echo Installing dependencies from pip
pipenv run pip install -r "$root/requirements.txt" -t ./
rm -rf ./*.dist-info/

echo "Copying source and config"
for inc in $includes; do
    cp -r "$root/$inc" .
done

echo "Creating ZIP"
# Allow restarting...
rm "$output" 2>/dev/null || true
zip -r $output * --exclude '*.pyc' --exclude '*__pycache__/' --exclude '*.po' --exclude '*~' --exclude '*.egg-info/*' $extras


echo "Cleaning up dependencies..."
rm "$root"/requirements*.txt

echo "Success! Created $output"
popd >/dev/null
