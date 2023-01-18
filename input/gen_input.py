import csv
import subprocess
import numpy as np
from datetime import datetime

ls = [6, 8, 14]
# ls = [12, 14, 16, 18, 20]
# ls = range(8, 14, 2)
# ls = range(6, 12, 2)
# ps = np.linspace(0.1, 0.5, 5)
# ps = np.linspace(0.008, 0.012, 5)
# ps = [0.013, 0.014, 0.016, 0.017, 0.018, 0.019]
# ps = np.linspace(0.013, 0.017, 5)
ps = np.linspace(0.003, 0.007, 5)
# ps = {
# 2 : np.linspace(0.001, 0.005, 5),
# 3 : np.linspace(0.002, 0.006, 5),
# 5 : np.linspace(0.004, 0.008, 5),
# 11 : np.linspace(0.006, 0.01, 5),
# 29 : np.linspace(0.007, 0.011, 5)
# }
# local_dims = [2, 3, 5, 11, 29]
# local_dims = [2, 3]
# cycles = [0, 1, 2, 4, 8]
cycles = [0, 4]
# cycles = [4, 8]
trials = 1e4
# decoder_m = 'mwpm'
# decoder_q = 'mwpm'
decoder_m = 'clus'
decoder_q = 'clus'
job = 0
git_hash = subprocess.check_output(['git', 'rev-parse',  'HEAD']).strip()
today = datetime.today().strftime('%Y-%m-%d')
repeats = 1

with open(f'{today}.csv', 'w') as csv_file:
    writer = csv.writer(csv_file, delimiter=',')
    writer.writerow(['l', 'local_dim', 'p',
                     'q', 'cycles', 'trials', 'decoder_m', 'decoder_q', 'cutoff', 'git_hash', 'job'])
    for cycle in cycles:
        for l in ls:
            cutoff = 2*l
            for local_dim in local_dims:
                # for p in ps[local_dim]:
                for p in ps:
                    for _ in range(repeats):
                        writer.writerow([l, local_dim, p, p,
                                        cycle, trials, decoder_m, decoder_q, cutoff, git_hash, job])
                        job += 1
