import json
import argparse
from pathlib import Path
import logging

import graph_tool.all as gt

parser = argparse.ArgumentParser(
    description='Compute excess edges in a graph.'
)
parser.add_argument(
    '--input',
    type=str,
    help='Path to the network file',
)
parser.add_argument(
    '--output',
    type=str,
    help='Path to the output JSON file',
)

args = parser.parse_args()

network_fp = Path(args.input)
output_fp = Path(args.output)

assert network_fp.exists(), f'File not found: {network_fp}'
assert network_fp.is_file(), f'Not a file: {network_fp}'
assert output_fp.parent.exists(), f'Directory not found: {output_fp.parent}'
assert output_fp.parent.is_dir(), f'Not a directory: {output_fp.parent}'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

logger.info(f'Input: {network_fp}')
logger.info(f'Output: {output_fp}')

G = gt.load_graph_from_csv(
    str(network_fp),
    directed=False,
    csv_options={'delimiter': '\t'},
)

n_edges = G.num_edges()

gt.remove_parallel_edges(G)
n_parallel_edges = n_edges - G.num_edges()

gt.remove_self_loops(G)
n_self_loops = n_edges - n_parallel_edges - G.num_edges()

logger.info(f'n_edges: {n_edges}')
logger.info(f'n_parallel_edges: {n_parallel_edges}')
logger.info(f'n_self_loops: {n_self_loops}')
logger.info(f'ratio_parallel_edges: {n_parallel_edges / n_edges}')
logger.info(f'ratio_self_loops: {n_self_loops / n_edges}')

with open(output_fp, 'w') as f:
    json.dump({
        'n_edges': n_edges,
        'n_parallel_edges': n_parallel_edges,
        'n_self_loops': n_self_loops,
        'ratio_parallel_edges': n_parallel_edges / n_edges,
        'ratio_self_loops': n_self_loops / n_edges,
    }, f, indent=4)
