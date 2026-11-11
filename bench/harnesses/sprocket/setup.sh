#!/usr/bin/env bash
# Prepares a fresh Ubuntu 24.04 x86_64 box for Sprocket runs. Run as the `ubuntu` user.
# Sign-in and the KiCad connector install happen afterwards (see README.md) because both need the account.
set -euo pipefail

SPROCKET_VERSION="${SPROCKET_VERSION:-0.5.0}"

export DEBIAN_FRONTEND=noninteractive
sudo apt-get update
sudo apt-get install -y ca-certificates curl git unzip build-essential \
	libfuse2t64 xvfb xauth libgl1 libegl1 libxkbcommon-x11-0 libnss3 fonts-dejavu-core

curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs

curl -fsSL https://bun.sh/install | bash

sudo npm install -g "usesprocket@${SPROCKET_VERSION}"
sprocket --version

mkdir -p ~/pcbbench-run ~/pcbbench-results
