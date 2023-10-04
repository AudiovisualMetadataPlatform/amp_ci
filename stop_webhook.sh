#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

if [ -e $SCRIPT_DIR/webhook.pid ]; then
    kill $(cat $SCRIPT_DIR/webhook.pid)
else
    echo webhook.pid does not exist
fi