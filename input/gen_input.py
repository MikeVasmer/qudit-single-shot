import csv
import subprocess
import numpy as np

ls = [4, 6, 8]
ps = np.linspace(0.003, 0.007, 3)
local_dim = 3
cycles = 2
trials = 1e3
# decoder_m = 'mwpm'
# decoder_q = 'mwpm'
decoder_m = 'clus'
decoder_q = 'clus'
job = 0
git_hash = subprocess.check_output(['git', 'rev-parse',  'HEAD']).strip()
repeats = 1

with open(f'example.csv', 'w') as csv_file:
    writer = csv.writer(csv_file, delimiter=',')
    writer.writerow(['l', 'local_dim', 'p',
                     'q', 'cycles', 'trials', 'decoder_m', 'decoder_q', 'cutoff', 'git_hash', 'job'])
    for l in ls:
        cutoff = 2*l
        for p in ps:
            for _ in range(repeats):
                writer.writerow([l, local_dim, p, p,
                                 cycles, trials, decoder_m, decoder_q, cutoff, git_hash, job])
                job += 1
