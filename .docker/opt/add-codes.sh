#!/bin/bash -e

# This script is executed whenever the docker container is (re)started.

# Debugging
set -x

# Environment
export SHELL=/bin/bash

# Activate conda.
__conda_setup="$('/opt/conda/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/opt/conda/etc/profile.d/conda.sh" ]; then
        . "/opt/conda/etc/profile.d/conda.sh"
    else
        export PATH="/opt/conda/bin:$PATH"
    fi
fi
unset __conda_setup

# Install raspa code.
verdi code show raspa@localhost || verdi code setup --config /opt/aiida-raspa/.docker/raspa-code.yml --non-interactive
