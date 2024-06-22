import os
import time
import json
import argparse

from src.utils import set_up, post_process
from src.constants import *


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--edgelist', type=str, required=True)
    parser.add_argument('--clustering', type=str, required=True)
    parser.add_argument('--output-folder', type=str, required=True)
    parser.add_argument('--seed', type=int, required=False, default=0)
    return parser.parse_args()


print('== Input == ')

args = parse_args()
edgelist_fn = args.edgelist
clustering_fn = args.clustering
output_dir = args.output_folder
seed = args.seed

print(f'Method: ABCD')
print(f'Network: {edgelist_fn}')
print(f'Clustering: {clustering_fn}')
print(f'Output folder: {output_dir}')
print(f'Seed: {seed}')

print('== Output == ')

logs = []

start = time.perf_counter()
set_up(
    edgelist_fn,
    clustering_fn,
    seed,
    output_dir,
    use_existing_clustering=True,
)
elapsed = time.perf_counter() - start
logs.append(f"Setup time: {elapsed}")

with open(f'{output_dir}/params.json', 'r') as f:
    params = json.load(f)
    seed = params['seed']
    xi = params['xi']

cmd = f'''
julia ABCDGraphGenerator.jl/utils/graph_sampler.jl \
    {output_dir}/{EDGE} {output_dir}/{COM_OUT} \
    {output_dir}/{DEG} {output_dir}/{CS} \
    xi {xi} false false {seed} 0
'''
logs.append(cmd)

start = time.perf_counter()
os.system(cmd)
elapsed = time.perf_counter() - start
logs.append(f"Generation time: {elapsed}")

start = time.perf_counter()
try:
    post_process(output_dir)
except Exception as e:
    logs.append(f"Post-process error: {e}")
elapsed = time.perf_counter() - start
logs.append(f"Post-process time: {elapsed}")

assert os.path.exists(output_dir)
log_f = open(f'{output_dir}/run.log', 'w')
for log in logs:
    log_f.write(log)
    log_f.write('\n')
log_f.close()
