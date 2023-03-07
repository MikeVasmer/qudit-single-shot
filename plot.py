from glob import glob
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

mpl.rcParams.update({'font.size': 12})

df = pd.DataFrame()
for file in glob('l=*.csv'):
    df_tmp = pd.read_csv(file)
    df = pd.concat([df, df_tmp], ignore_index=True)
df = df.sort_values(by=['p'])

kappa = 1.96
df['pfail'] = (df['fails'] + (kappa**2 / 2)) / (df['trials'] + kappa**2)
df['err'] = kappa * \
    np.sqrt(df['pfail'] * (1 - df['pfail']) / (df['trials'] + kappa**2))

for l in [4, 6, 8]:
    df_l = df[(df['l'] == l)]
    (_, caps, _) = plt.errorbar('p', f'pfail', f'err', data=df_l,
                                linestyle='dashed', marker='o', markersize=6, label=f'L={l}', capsize=5)
    for cap in caps:
        cap.set_markeredgewidth(1)
ax = plt.gca()
ax.legend(loc='lower right')
ax.set_yscale('log')
ax.grid(True)
ax.set(xlabel='$p$', ylabel='$p_{\mathrm{fail}}$',
       xticks=[0.003, 0.005, 0.007])
plt.show()
