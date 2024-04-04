import sys
import json

import pandas as pd

network_id = sys.argv[1]
resolution = sys.argv[2]
method = sys.argv[3]
based_on = sys.argv[4]

print(
    f'Degree distribution for {network_id} at resolution {resolution} using {method}')

_dir = f'data/networks/{method}/{based_on}/{network_id}/leiden{resolution}/'

if 'abcd' in method:
    # == Compute input degree distribution ==
    deg_fn = 'deg.dat'

    with open(f'{_dir}/{deg_fn}') as f:
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
    edge_fn = 'edge.dat'

    with open(f'{_dir}/{edge_fn}') as f:
        edges = [x.strip().split('\t') for x in f.readlines()]

    neighbors = {}
    for u, v in edges:
        neighbors.setdefault(u, [])
        neighbors[u].append(v)

        neighbors.setdefault(v, [])
        neighbors[v].append(u)

    degrees = [len(neighbors[u]) for u in neighbors]
    df_gen = pd.DataFrame(degrees, columns=['degree'])

    # Compute the quantiles
    q1_gen = df_gen['degree'].quantile(0.25)
    q3_gen = df_gen['degree'].quantile(0.75)
    med_gen = df_gen['degree'].median()
    min_gen = df_gen['degree'].min()
    max_gen = df_gen['degree'].max()
    mean_gen = df_gen['degree'].mean()

    # Compute the frequency
    df_gen = df_gen.groupby('degree').size().reset_index(name='count_gen')

    # == Plot the degree distributions ==

    import matplotlib.pyplot as plt
    import seaborn as sns

    fig, ax = plt.subplots(1, 1, figsize=(5, 5), dpi=300, tight_layout=True)
    sns.scatterplot(ax=ax, data=df, x='degree',
                    y='count', label='Input', alpha=0.8)
    sns.scatterplot(ax=ax, data=df_gen, x='degree',
                    y='count_gen', label='Generated', alpha=0.8)
    ax.set_xlabel('Degree')
    ax.set_ylabel('Count')
    ax.legend()
    ax.set_xscale('log')
    ax.set_yscale('log')
    plt.savefig(f'{_dir}/deg_dist.png')

    # Output as JSON file
    with open(f'{_dir}/deg_dist.json', 'w') as f:
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
else:
    edge = 'edge' if 'abcd' in method else 'network'
    com = 'com' if 'abcd' in method else 'community'
