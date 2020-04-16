#!/bin/bash -e

# This script is executed whenever the docker container is (re)started.

# Debugging
set -x

# Environment
export SHELL=/bin/bash

# Install raspa code.
verdi code show raspa@localhost || verdi code setup --config /opt/aiida-raspa/.docker/raspa-code.yml --non-interactive
