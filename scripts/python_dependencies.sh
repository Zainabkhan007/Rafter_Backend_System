#!/usr/bin/env bash

sudo chown -R ubuntu:ubuntu ~/rafters_food
virtualenv /home/ubuntu/rafters_food/venv
source /home/ubuntu/rafters_food/venv/bin/activate
pip install -r /home/ubuntu/rafters_food/requirements.txt