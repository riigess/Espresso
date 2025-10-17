#!/bin/bash

proj_dir=$(dirname "$0")
if [[ "$(echo -n $proj_dir | wc -m)" -eq 1 ]]; then
    proj_dir="$(pwd)"
fi
proj_name="Espresso"
if [[ -z "$(echo $proj_dir | grep $proj_name)" ]]; then
    proj_dir=$proj_dir/$proj_name
fi
echo "Proj_dir: $proj_dir"

runner() {
    cd $proj_dir
    if [ -f .venv/bin/activate ]; then
        echo ".venv exists (check passed)"
        source .venv/bin/activate
        if [[ -z "$(pip3 list | grep discord)" ]]; then
            pip3 install -r requirements.txt
        fi
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
direct="$proj_dir"
if [[ -z "$(echo $direct | grep $proj_name)" ]]; then
    direct="$proj_dir/$proj_name"
fi
psresp=""
if [[ "$(uname)" == "Darwin" ]]; then
    psresp="$(ps -a)"
elif [[ "$(uname)" == "Linux" ]]; then
    psresp="$(ps -auxe)"
else
    echo "Windows is currently unsupported...exiting"
    exit -1
fi
if [[ -z "$(echo -n $psresp | grep "python3" | grep "PWD=$direct" | grep -v grep)" ]]; then
    runner
else
    echo "Already running"
fi
