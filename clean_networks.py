import os
import sys
import argparse
from pathlib import Path

import graph_tool.all as gt


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--edgelist', type=str, required=True)
    parser.add_argument('--output', type=str, required=True)
    return parser.parse_args()


def clean_network(edgelist_fp, output_fp):
    g = gt.load_graph_from_csv(input_network, csv_options={'delimiter': '\t'})
    gt.remove_parallel_edges(g)
    gt.remove_self_loops(g)

    # Write edgelist to TSV
    with open(output_fp, 'w') as f:
        for e in g.edges():
            f.write(f"{g.vp.name[e.source()]}\t{g.vp.name[e.target()]}\n")


args = parse_args()
edgelist_fp = args.edgelist
output_dir = Path(args.output)

output_dir.mkdir(parents=True, exist_ok=True)

clean_network(
    edgelist_fp,
    output_fp,
)
