#!/usr/bin/env bash

source venv/bin/activate

python input/gen_input.py
python monte_carlo.py example.csv 0 8
python plot.py
