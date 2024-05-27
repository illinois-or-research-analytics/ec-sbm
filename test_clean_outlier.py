import argparse
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-network",
        type=str,
        required=True,
        help="Output network",
    )
    parser.add_argument(
        "--output-clustering",
        type=str,
        required=True,
        help="Output clustering",
    )
    return parser.parse_args()


args = parse_args()
edgelist_fp = Path(args.output_network)
clustering_fp = Path(args.output_clustering)

nodes_in_clustering = set()
with open(clustering_fp) as f:
    for line in f:
        node, _ = line.strip().split()
        nodes_in_clustering.add(node)

with open(edgelist_fp) as f:
    for line in f:
        node1, node2 = line.strip().split()
        assert node1 in nodes_in_clustering, \
            f'Node {node1} is not clustered'
        assert node2 in nodes_in_clustering, \
            f'Node {node2} is not clustered'

print('Test passed!')
