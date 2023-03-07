# qudit-single-shot

Code for reproducing the numerical results described in

J. C. Bridgeman, A. Kubica and M. Vasmer, "3D subsystem codes from 2D topological codes", [arXiv:23xx.xxxx](https://arxiv.org)

## Setup

`pip install -r requirements.txt`

Note: if using on a cluster it may be necessary to update CMake, gcc and the rust compiler

## Example

See `example.sh` for a qutrit simulation example

## Usage

Use `gen_input.py` in `input` folder to make parameter files, then run the simulation(s) using `monte_carlo.py`
