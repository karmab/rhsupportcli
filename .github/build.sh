#!/bin/bash

set -ex
. venv/bin/activate

mkdir -p src/rhsupportlib/version
git rev-parse --short HEAD > src/rhsupportlib/version/git
podman build -t quay.io/karmab/rhsupportcli -f Dockerfile .

podman login -u $QUAY_USERNAME -p $QUAY_PASSWORD quay.io
podman push quay.io/karmab/rhsupportcli:latest

export VERSION=$(date "+%Y%m%d%H%M")
sed -i "s/99.0/99.0.$VERSION/" pyproject.toml
python3 -m build
twine upload --repository-url https://upload.pypi.org/legacy/ -u __token__ -p $PYPI_TOKEN --skip-existing dist/*
