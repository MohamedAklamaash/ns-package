#!/usr/bin/bash
set -e
KEY="$HOME/.ssh/psg_fedora_vm"
HOST="test@192.168.122.90"
SRC="/home/aklamaash/Documents/college/sem9/ns_package/hypernet/"
rsync -az -e "ssh -i $KEY -o BatchMode=yes" --exclude .venv --exclude .git --exclude __pycache__ --exclude .pytest_cache "$SRC" "$HOST:~/ns_package/hypernet/"
ssh -i "$KEY" -o BatchMode=yes "$HOST" "cd ~/ns_package/hypernet && HYPERNET_DATA=~/ns_package/datasets HYPERNET_RESULTS=~/ns_package/results $*"
