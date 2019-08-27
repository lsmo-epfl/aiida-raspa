#!/bin/bash -e

# This script is executed whenever the docker container is (re)started.

# Debugging
set -x

# Environment
export SHELL=/bin/bash

# Install the ddec and cp2k codes
RASPA_FOLDER=/home/aiida/code/aiida-raspa

verdi code show raspa@localhost || verdi code setup --config ${RASPA_FOLDER}/.docker/raspa-code.yml --non-interactive
