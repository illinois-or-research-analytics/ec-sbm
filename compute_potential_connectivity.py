import sys
import csv
import json

import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

from utils import process_stats_to_params
from constants import *

network_id = sys.argv[1]
resolution = sys.argv[2]
method = sys.argv[3]
based_on = sys.argv[4]

print(
    f'Statisctics for {network_id} at resolution {resolution} using {method}')

_dir = f'data/networks/{method}/{based_on}/{network_id}/leiden{resolution}/'

if 'abcd' in method:
    with open(f'{_dir}/{PARAMS}') as f:
        xi = json.load(f)['xi']
else:
    network_stats_json_path = f'data/network_params/{
        network_id}_leiden{resolution}.json'
    _, _, _, _, xi, _, _, _, _ = \
        process_stats_to_params(network_stats_json_path, 0)

edge = EDGE if 'abcd' in method else 'network.dat'
com = COM_OUT if 'abcd' in method else 'community.dat'

node2degree = {}
if 'abcd' in method:
    node_mapping = dict()
    with open(f'{_dir}/{NODE_ID}') as f:
        reader = csv.reader(f, delimiter='\t')
        for node, node_id in reader:
            node_mapping[int(node)] = node_id

    with open(f'{_dir}/{DEG}') as f:
        for i, line in enumerate(f.readlines()):
            node2degree[node_mapping[i + 1]] = int(line.strip())
else:
    f = open(f'{_dir}/{edge}')
    reader = csv.reader(f, delimiter='\t')
    G = nx.read_edgelist([
        ' '.join(x) for x in reader
    ])
    f.close()

    for u in G.nodes:
        node2degree[u] = len(G[u])

comm2nodes = {}
with open(f'{_dir}/{com}') as f:
    reader = csv.reader(f, delimiter='\t')
    for node, comm in reader:
        comm2nodes.setdefault(comm, [])
        comm2nodes[comm].append(node)

potential_connectivity = []
for comm, nodes in comm2nodes.items():
    total_deg = sum([node2degree[node] for node in nodes])
    potential_connectivity.append(total_deg * (1 - xi) / (2 * len(nodes)))

EPS = 1e-8
bins = np.arange(
    0, max(potential_connectivity) + EPS, 0.1) + EPS
bins[0] -= EPS

fig, ax = plt.subplots(1, 1, figsize=(8, 8), dpi=300)
ax.hist(potential_connectivity, bins=bins)
ax.set_xlabel('number of edges / (comm size - 1)')
ax.set_ylabel('count')
ax.axvline(1.0, color='red')
fig.tight_layout()
fig.savefig(f'{_dir}/potential_connectivity_hist.pdf')

total_edges, sizes_minus_one = [], []
for comm, nodes in comm2nodes.items():
    total_edges.append(sum([node2degree[node] for node in nodes]) * (1 - xi))
    sizes_minus_one.append(len(nodes) - 1)

fig, ax = plt.subplots(1, 1, figsize=(5, 5), dpi=300)
ax.scatter(total_edges, sizes_minus_one)
ax.set_xlabel('number of edges')
ax.set_ylabel('community size - 1')
m = min(min(total_edges), min(sizes_minus_one)) - 0.25
M = max(max(total_edges), max(sizes_minus_one)) + 0.25
ax.set_xlim(m, M)
ax.set_ylim(m, M)
ax.set_aspect('equal')
ax.plot([0, 1], [0, 1], transform=ax.transAxes, color='red')
fig.tight_layout()
fig.savefig(f'{_dir}/potential_connectivity_scatter.png')

with open(f'{_dir}/potential_connectivity.log', 'w') as f:
    wellconnected = len(
        [x for x in potential_connectivity if x > 1.0])
    f.write(
        f'Well connected: {wellconnected} / {len(potential_connectivity)} = {wellconnected / (len(potential_connectivity))}\n')

    disconnected = len(
        [x for x in potential_connectivity if x < EPS])
    f.write(
        f'Disconnected: {disconnected} / {len(potential_connectivity)} = {disconnected / (len(potential_connectivity))}\n')
