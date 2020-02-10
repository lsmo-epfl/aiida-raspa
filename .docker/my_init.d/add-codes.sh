#!/bin/bash
set -em

su -c /opt/add-codes.sh ${SYSTEM_USER}

# Make /opt/aiida-raspa folder editable for the $SYSTEM_USER.
chown -R ${SYSTEM_USER}:${SYSTEM_USER} /opt/aiida-raspa/
