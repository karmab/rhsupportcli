#!/bin/bash

set -ex

mkdir -p src/rhsupportlib/version
git rev-parse --short HEAD > src/rhsupportlib/version/git
podman build -t quay.io/karmab/rhsupportcli -f Dockerfile .

podman login -u $QUAY_USERNAME -p $QUAY_PASSWORD quay.io
podman push quay.io/karmab/rhsupportcli:latest
