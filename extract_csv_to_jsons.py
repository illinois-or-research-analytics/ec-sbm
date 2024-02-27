import os

import pandas as pd

stats = pd.read_csv('data/network_params_lfr.csv')
del stats['Unnamed: 0']
stats.head()

os.system(f'mkdir -p data/network_params/')
for row_id, row in stats.iterrows():
    name = row['name'].replace('.tsv', '')
    row.to_json(f'data/network_params/{name}.json')
