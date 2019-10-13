#!/usr/bin/env bash
set -e

if [[ -z "${VERSION}" ]] ; then
    echo "Version not defined ";
    exit 1
fi

echo "version ${VERSION}"

printf "[distutils]\nindex-servers = pypi \n[pypi]\nusername:${PYPI_USER}\npassword:${PYPI_PASSWORD}\n" > ~/.pypirc


sed -i  's/VERSION = .*/'VERSION="'${VERSION}'"'/' ussd/__init__.py

python setup.py sdist

git checkout ussd/__init__.py

twine upload dist/*
