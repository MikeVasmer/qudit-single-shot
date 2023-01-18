import string
import numpy as np
import csv
from datetime import datetime
from tqdm import tqdm
import pandas as pd
import argparse
from src.clustering import Clustering
from src.graph import build_matching_graph
from pymatching import Matching
import random


def monte_carlo(l: int, local_dim: int, p: float, q: float, cycles: int, trials: int, decoder_m: string, decoder_q: string, cutoff: int, job: int, git_hash: string, debug: bool):
    # Setup
    mats = np.load(f'matrices/3d_stc_l{l}.npz')
    gx = mats['gx']  # X gauge
    gz = mats['gz']  # Z gauge
    hx = mats['hx']  # X stabilizer
    lx = mats['lxb']  # X (bare) logical
    rx = mats['rx']  # X relations
    tx = mats['tx']  # X flux -> synd map
    matching_graph_hx = build_matching_graph(hx, p)
    matching_graph_rx = build_matching_graph(rx, q)
    num_rels, num_checks = rx.shape
    num_stabs, num_qudits = hx.shape
    if decoder_m == 'mwpm':
        matching_rx = Matching(matching_graph_rx)
    elif decoder_m == 'clus':
        clustering_rx = Clustering(
            rx, matching_graph_rx, num_checks, local_dim, cutoff)
    if decoder_q == 'mwpm':
        matching_hx = Matching(matching_graph_hx)
    elif decoder_q == 'clus':
        clustering_hx = Clustering(
            hx, matching_graph_hx, num_qudits, local_dim, cutoff)
    fails = 0
    timeouts = 0
    # Simulation loop
    for _ in tqdm(range(int(trials))):
        qudits = np.zeros(num_qudits, dtype=np.int32)
        flux = np.zeros(num_checks, dtype=np.int32)
        synd_r = np.zeros(num_rels, dtype=np.int32)
        synd_h = np.zeros(num_stabs, dtype=np.int32)
        for _ in range(cycles):
            # Randomize the gauge
            indices = [i for i in range(num_checks) if random.random() > 0.5]
            gauge_op = np.sum(gz[indices], axis=0)
            qudits = np.mod(qudits + gauge_op, local_dim)
            # iid qudit (Z) error
            random_op = np.random.randint(1, local_dim, size=num_qudits)
            error_locs = np.random.rand(num_qudits) <= p
            error = np.multiply(random_op, error_locs)
            qudits = np.mod(qudits + error, local_dim)
            # Calculate flux
            flux = np.mod(np.matmul(gx, qudits), local_dim)
            # iid measurement error
            random_op = np.random.randint(1, local_dim, size=num_checks)
            error_locs = np.random.rand(num_checks) <= q
            error = np.multiply(random_op, error_locs)
            flux = np.mod(flux + error, local_dim)
            # Calculate relation syndrome
            synd_r = np.mod(np.matmul(rx, flux), local_dim)
            # Flux validations
            if decoder_m == 'mwpm':
                corr_f = matching_rx.decode(synd_r)
            elif decoder_m == 'clus':
                corr_f = clustering_rx.decode(synd_r)
            flux = np.mod(flux + corr_f, local_dim)
            # Calculate stabilizer syndrome
            synd_h = np.mod(np.matmul(tx, flux), local_dim)
            # Qudit correction
            if decoder_q == 'mwpm':
                corr_q = matching_hx.decode(synd_h)
            elif decoder_q == 'clus':
                corr_q = clustering_hx.decode(synd_h)
            qudits = np.mod(qudits + corr_q, local_dim)
        # Randomize the gauge
        indices = [i for i in range(num_checks) if random.random() > 0.5]
        gauge_op = np.sum(gz[indices], axis=0)
        qudits = np.mod(qudits + gauge_op, local_dim)
        # iid qudit error
        random_op = np.random.randint(1, local_dim, size=num_qudits)
        error_locs = np.random.rand(num_qudits) <= p
        error = np.multiply(random_op, error_locs)
        qudits = np.mod(qudits + error, local_dim)
        # Calculate stabilizer syndrome
        synd_h = np.mod(np.matmul(hx, qudits), local_dim)
        # Qudit correction
        if decoder_q == 'mwpm':
            corr_q = matching_hx.decode(synd_h)
        elif decoder_q == 'clus':
            corr_q = clustering_hx.decode(synd_h)
        qudits = np.mod(qudits + corr_q, local_dim)
        # Check for a logical error
        synd_h = np.mod(np.matmul(hx, qudits), local_dim)
        if debug and decoder_q == 'mwpm':
            assert not np.any(synd_h)
        if np.any(synd_h):
            fails += 1
            timeouts += 1
        else:
            fails += np.any(np.mod(np.matmul(lx, qudits), local_dim))
    # Save results
    today = datetime.today().strftime('%Y-%m-%d')
    with open(f'l={l}_p={p}_q={q}_d={local_dim}_cycles={cycles}_trials={trials}_{today}_j{job}.csv', 'w') as out_file:
        writer = csv.writer(out_file, delimiter=',')
        writer.writerow(['l', 'local_dim', 'p',
                        'q', 'cycles', 'trials', 'decoder_m', 'decoder_q', 'cutoff', 'fails', 'timeouts', 'git_hash', 'job'])
        writer.writerow([l, local_dim, p, q, cycles,
                        trials, decoder_m, decoder_q, cutoff, fails, timeouts, git_hash, job])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Simulation of single-shot error correction using the 3d subsystem toric code.')
    parser.add_argument(
        'input_file', help='path to csv input file containing run parameters')
    parser.add_argument(
        'start_row', type=int, help='first row of parameters to run')
    parser.add_argument(
        'end_row', type=int, help='last row of parameters to run')

    args = parser.parse_args()
    path = args.input_file
    start_row = args.start_row
    end_row = args.end_row

    print(random.random())
    df = pd.read_csv(path)
    j = 1
    for i in range(start_row, end_row+1):
        row = df.iloc[[i]].squeeze()
        print(row)
        l = row['l']
        local_dim = row['local_dim']
        p = row['p']
        q = row['q']
        cycles = row['cycles']
        trials = row['trials']
        decoder_m = row['decoder_m']
        decoder_q = row['decoder_q']
        cutoff = row['cutoff']
        job = row['job']
        git_hash = row['git_hash']
        debug = False
        monte_carlo(l, local_dim, p, q, cycles,
                    trials, decoder_m, decoder_q, cutoff, job, git_hash, debug)
        print(f'Job {j} of {end_row-start_row+1} complete.')
        j += 1
