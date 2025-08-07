#!/bin/bash

proj_dir=$(dirname "$0")
proj_name="Espresso"

runner() {
    cd $proj_dir/$proj_name
    if [ -f .venv/bin/activate ]; then
        echo ".venv exists (check passed)"
        source .venv/bin/activate
    else
        echo ".venv does not exist (check not passed)"
        python3 -m venv .venv
        source .venv/bin/activate
        pip3 install -r requirements.txt
    fi
    echo "Updating directory with git"
    git pull
    cd src
    echo "Starting bot"
    python3 main.py
    runner
}

# If there is nothing running in /root/luna/src
if [[ -z "$(ps -auxe | grep "python3" | grep "PWD=$proj_dir/$proj_name/src" | grep -v grep)" ]]; then
    runner
else
    echo "Already running"
fi
