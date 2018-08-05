#!/usr/bin/env bash
# Builds the squeeze-alexa codebase:
#   * compiling translations
#   * copying source, config, docs and scripting to a dist/ folder
#   * extracting and cleaning runtime dependencies (using pip)
set -e

root=$(readlink -f "$(dirname $0)/..")
includes="handler.py squeezealexa/ locale/ etc/ metadata/ bin docs/ README.md"

pushd "$root" >/dev/null
dist_dir="$PWD/dist"
echo "Building to $dist_dir..."

$root/bin/update-translations

$root/bin/compile-translations

echo "Installing Pipenv dependencies..."
pipenv install --dev >/dev/null
pipenv run pipenv_to_requirements -f

[ -e "$dist_dir" ] && rm -rf "$dist_dir"
mkdir "$dist_dir"
cd "$dist_dir"

echo Installing dependencies from pip
pipenv run pip install -r "$root/requirements.txt" -t ./

echo "Cleaning up"
rm "$root"/requirements*.txt
rm -rf ./*.dist-info/

echo "Copying source and config"
for inc in $includes; do
    cp -r "$root/$inc" "./$inc"
done

popd >/dev/null
