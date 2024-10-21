import csv
import argparse
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
clustering = dict()
with open(inp_clustering_fp) as f:
    for line in f:
        node, cluster = line.strip().split()
        clustering.setdefault(cluster, set()).add(node)

# Save new clustering file
clustered_nodes = set()
out_clustering_fn = Path(inp_clustering_fp).name
with open(out_dir / out_clustering_fn, "w") as out_f:
    with open(inp_clustering_fp) as f:
        csv_reader = csv.reader(f, delimiter="\t")
        csv_writer = csv.writer(out_f, delimiter="\t")

        for node, cluster in csv_reader:
            assert cluster in clustering
            assert node not in clustered_nodes
            if len(clustering[cluster]) > 1:
                clustered_nodes.add(node)
                csv_writer.writerow([node, cluster])

# Save new network file
out_network_fn = Path(inp_network_fp).name
with open(out_dir / out_network_fn, "w") as out_f:
    with open(inp_network_fp) as f:
        csv_writer = csv.writer(out_f, delimiter="\t")
        csv_reader = csv.reader(f, delimiter="\t")

        for node1, node2 in csv_reader:
            if node1 in clustered_nodes and node2 in clustered_nodes:
                csv_writer.writerow([node1, node2])
