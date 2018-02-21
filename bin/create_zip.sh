#!/usr/bin/env bash
set -e

output="upload.zip"

cd "$(dirname $0)/.."
pip --isolated download -r requirements.txt

deps=$(cut -d'=' -f1 requirements.txt | tr '\n' ' ')
echo "Processing $deps"
for dep in $deps; do
    [ -d $dep ] || unzip $dep-*.whl >/dev/null
done

# Allow restarting...
rm "$output" 2>/dev/null || true

zip -r upload.zip squeezealexa/ $deps LICENSE *.py *.pem --exclude '*.pyc' --exclude '*~' --exclude __pycache__

echo "Cleaning up dependencies..."
for dep in $deps; do
    rm -rf "./$dep/"
    rm -rf ./$dep-*.dist-info/
done
rm -f ./*.whl

echo "Success! Created $output"
