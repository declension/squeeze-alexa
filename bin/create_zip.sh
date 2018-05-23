#!/usr/bin/env bash
set -e
# TODO: migrate this to Python, it's much too big now

includes="handler.py squeezealexa/ locale/ etc/"

root=$(readlink -f "$(dirname $0)/..")

# Just like lambda-uploader uses...
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
pipenv run -- pip --isolated download --no-deps -r "$root/requirements.txt"

deps=$(grep -r -v '^#' "$root/requirements.txt" | cut -d'=' -f1 | tr '\n' ' ')
echo "Processing: $deps"
for dep in $deps; do
    echo "Processing '$dep'"
    whl=$dep-*.whl
    [ -f $whl ] && unzip -q -o $whl
    # Copy with things like paho-mqtt-1.3.1.tar.gz having paho-1.3.1/src
    tarfile=$dep-*.tar.gz
    [ -f $tarfile ] && tar -xf $tarfile && mv $dep-*/src/* ./ && rm -rf ./$dep-*/ && echo "Extracted $dep"
done

echo "Copying source and config"
for inc in $includes; do
    cp -r "$root/$inc" .
done


echo "Cleaning up dependencies..."
for dep in $deps; do
    rm -rf ./$dep-*.whl
    rm -rf ./$dep-*.tar.gz
    rm -rf ./$dep-*/
    rm -rf ./$dep-*.dist-info/
done


echo "Creating ZIP"
# Allow restarting...
rm "$output" 2>/dev/null || true
zip -r $output * --exclude '*.pyc' --exclude '*__pycache__/' --exclude '*.po' --exclude '*~' --exclude '*.egg-info/*' $extras


echo "Cleaning up dependencies..."
rm "$root"/requirements*.txt

echo "Success! Created $output"
popd >/dev/null
