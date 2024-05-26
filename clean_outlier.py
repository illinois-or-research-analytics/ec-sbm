import csv
import argparse
import shutil
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Clean outlier data")
    parser.add_argument(
        "--input-network",
        type=str,
        required=True,
        help="Input network",
    )
    parser.add_argument(
        "--input-clustering",
        type=str,
        required=True,
        help="Input clustering",
    )
    parser.add_argument(
        "--output-folder",
        type=str,
        required=True,
        help="Output folder",
    )
    return parser.parse_args()


args = parse_args()
inp_network_fp = Path(args.input_network)
inp_clustering_fp = Path(args.input_clustering)
out_dir = Path(args.output_folder)

out_dir.mkdir(parents=True, exist_ok=True)

# Compute all clustered nodes
clustered_nodes = set()
with open(inp_clustering_fp) as f:
    for line in f:
        node, _ = line.strip().split()
        clustered_nodes.add(node)

# Copy clustering file to output folder
shutil.copy(inp_clustering_fp, out_dir)

# Remove unclustered node from edgelists
with open(inp_network_fp) as f:
    edges = []
    for line in f:
        node1, node2 = line.strip().split()
        if node1 in clustered_nodes and node2 in clustered_nodes:
            edges.append((node1, node2))

out_network_fn = Path(inp_network_fp).name
with open(out_dir / out_network_fn, "w") as out_f:
    csv_writer = csv.writer(out_f, delimiter="\t")
    csv_writer.writerows(edges)
