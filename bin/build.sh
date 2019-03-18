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
echo "Building to $dist_dir"

echo "Installing Dev dependencies..."
poetry install >/dev/null

echo "Installing runtime dependencies with pip..."
# TODO: safer / prettier way of generating requirements.txt
poetry show --no-dev | sed -r 's/(\S+)\s+(\S+).*/\1==\2/' > requirements.txt

[ -e "$dist_dir" ] && rm -rf "$dist_dir"
mkdir "$dist_dir" && cd "$dist_dir"

poetry run pip install -q -r "$root/requirements.txt" -t ./

echo "Cleaning up..."
rm "$root"/requirements*.txt
rm -rf ./*.dist-info/

echo "Copying source and config..."
for inc in $includes; do
    cp -r "$root/$inc" "./$inc"
done

echo "Compiling translations..."
"$root/bin/compile-translations"

popd >/dev/null
