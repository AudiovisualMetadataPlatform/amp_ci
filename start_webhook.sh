#!/bin/bash

export SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

if [ -e $SCRIPT_DIR/environment.sh ]; then
    source $SCRIPT_DIR/environment.sh
fi

printenv

$SCRIPT_DIR/webhook -logfile $SCRIPT_DIR/webhook.log \
    -pidfile $SCRIPT_DIR/webhook.pid \
    -port 8196 \
    -hooks $SCRIPT_DIR/amp.yaml \
    -urlprefix webhook \
    -template \
    -debug


