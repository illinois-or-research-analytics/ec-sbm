import os
import json
import argparse

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from src.constants import *


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--network-folder', type=str, required=True)
    parser.add_argument('--output-folder', type=str, required=True)
    return parser.parse_args()


print('Evaluation')
print('== Input == ')

args = parse_args()
network_dir = args.network_folder
output_dir = args.output_folder

print(f'Network/Clustering: {network_dir}')
print(f'Output: {output_dir}')

print('== Output == ')

assert os.path.exists(network_dir)
os.makedirs(output_dir, exist_ok=True)

# == Compute input degree distribution ==
with open(f'{network_dir}/{DEG}') as f:
    degrees = [int(x.strip()) for x in f.readlines()]
    df = pd.DataFrame(degrees, columns=['degree'])

# Compute the quantiles
q1 = df['degree'].quantile(0.25)
q3 = df['degree'].quantile(0.75)
med = df['degree'].median()
min_ = df['degree'].min()
max_ = df['degree'].max()
mean = df['degree'].mean()

# Compute the frequency
df = df.groupby('degree').size().reset_index(name='count')

# == Compute generated degree distribution ==
with open(f'{network_dir}/degree.distribution') as f:
    degrees = [int(x.strip()) for x in f.readlines()]
    df_gen = pd.DataFrame(degrees, columns=['degree'])

# Compute the quantiles
q1_gen = df_gen['degree'].quantile(0.25)
q3_gen = df_gen['degree'].quantile(0.75)
med_gen = df_gen['degree'].median()
min_gen = df_gen['degree'].min()
max_gen = df_gen['degree'].max()
mean_gen = df_gen['degree'].mean()

# Compute the frequency
df_gen = df_gen.groupby('degree').size().reset_index(name='count')

# == Plot the degree distributions ==
fig, ax = plt.subplots(1, 1, figsize=(5, 5), dpi=300, tight_layout=True)
sns.scatterplot(ax=ax, data=df, x='degree',
                y='count', label='Input', alpha=0.5)
sns.scatterplot(ax=ax, data=df_gen, x='degree',
                y='count', label='Generated', alpha=0.5)
ax.set_xlabel('Degree')
ax.set_ylabel('Count (log)')
ax.legend()
ax.set_xscale('log')
ax.set_yscale('log')
plt.savefig(f'{output_dir}/deg_dist.png')
plt.clf()
plt.close()

# Output as JSON file
with open(f'{output_dir}/deg_dist.json', 'w') as f:
    json.dump({
        'input': {
            'min': min_,
            'q1': q1,
            'med': med,
            'q3': q3,
            'max': max_,
            'mean': mean
        },
        'generated': {
            'min': min_gen,
            'q1': q1_gen,
            'med': med_gen,
            'q3': q3_gen,
            'max': max_gen,
            'mean': mean_gen
        }
    }, f)
