import os
import time
import json
import argparse

from src.utils import set_up, post_process
from src.constants import *


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--network-id', type=str, required=True)
    parser.add_argument('--resolution', type=str, required=True)
    parser.add_argument('--method', type=str, required=True)
    parser.add_argument('--based_on', type=str, required=True)
    parser.add_argument('--seed', type=int, required=False, default=0)
    return parser.parse_args()


args = parse_args()
network_id = args.network_id
resolution = args.resolution
method = args.method
based_on = args.based_on
seed = args.seed

output_dir = set_up(
    method,
    based_on,
    network_id,
    resolution,
    seed,
    use_existing_clustering=True,
)

with open(f'{output_dir}/params.json', 'r') as f:
    params = json.load(f)
    seed = params['seed']
    xi = params['xi']

# == Generate ABCD network
print(
    f'ABCD-TA-MCS(network={network_id}, resolution={resolution})')
print(f'Seed: {seed}')
print(f'Mixing parameter (xi): {xi}')

cmd = f'julia ABCDGraphGenerator.jl/utils/graph_sampler_{method}.jl \
                {output_dir}/{EDGE} {output_dir}/{COM_OUT} \
                {output_dir}/{DEG} {output_dir}/{CS} \
                xi {xi} false false {seed} 0 \
                {output_dir}/{COM_INP} {output_dir}/{MCS}'

with open(f'{output_dir}/run.log', 'w') as f:
    f.write(cmd)
    f.write('\n')

    start = time.perf_counter()
    os.system(cmd)
    post_process(output_dir)
    elapsed = time.perf_counter() - start

    f.write(f"Generation time: {elapsed}")
