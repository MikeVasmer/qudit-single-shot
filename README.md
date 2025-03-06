# qudit-single-shot

Code for reproducing the numerical results described in

J. C. Bridgeman, A. Kubica, and M. Vasmer, Lifting topological codes: Three-dimensional subsystem codes from two-dimensional anyon models, *PRX Quantum* 5, 020310 (2024). [DOI](https://doi.org/10.1103/PRXQuantum.5.020310)

Interactive figures from the paper are avalable [here](https://mikevasmer.github.io/qudit-single-shot/)

## Setup

`pip install -r requirements.txt`

Note: if using on a cluster it may be necessary to update CMake, gcc and the rust compiler

## Example

See `example.sh` for a qutrit simulation example

## Usage

Use `gen_input.py` in `input` folder to make parameter files, then run the simulation(s) using `monte_carlo.py`
