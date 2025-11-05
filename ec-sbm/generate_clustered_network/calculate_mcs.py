import os
import csv
import json
import logging
import argparse
from collections import defaultdict

import networkx as nx
from hm01.graph import IntangibleSubgraph
from hm01.mincut import viecut
import time

# --- Constants from setup.cpp ---
# These are the keys used in progress_tracker.json
NODE_ID_KEY = "node_id"
COM_INP_KEY = "com_inp"
MCS_KEY = "mcs"

# --- Logging Setup ---
# (Setup is done in main to get output_dir)

# --- Graph and Cluster Functions ---


def read_node_id_mapping(node_id_path):
    """Reads the node_id.csv file and returns a 1-indexed string-to-int map."""
    node_id_map = {}
    with open(node_id_path, "r") as f:
        csv_reader = csv.reader(f, delimiter="\t")
        for i, row in enumerate(csv_reader):
            if row:
                node_id_map[row[0]] = i + 1  # 1-indexed
    return node_id_map


def read_graph_and_add_nodes(edgelist_fn, node_id_map):
    """
    Reads the original edgelist and ensures all nodes from the node_id_map
    (including 0-degree nodes) are added to the graph.
    """
    logging.info(f"Reading graph from {edgelist_fn}...")
    # Read graph using original string IDs
    G = nx.read_edgelist(edgelist_fn, create_using=nx.Graph, nodetype=str)
    logging.info(
        f"Graph read complete. {G.number_of_nodes()} nodes, {G.number_of_edges()} edges."
    )

    nodes_in_graph = set(G.nodes())
    nodes_to_add = []
    for node_str in node_id_map.keys():
        if node_str not in nodes_in_graph:
            nodes_to_add.append(node_str)

    if nodes_to_add:
        logging.info(
            f"Adding {len(nodes_to_add)} zero-degree nodes from clustering to graph..."
        )
        G.add_nodes_from(nodes_to_add)

    logging.info(
        f"Ensured all {len(node_id_map)} nodes from mapping exist in graph. G now has {G.number_of_nodes()} nodes."
    )
    return G


def from_existing_clustering(filepath):
    """
    FIXED: Reads the com_inp.csv file and correctly constructs
    IntangibleSubgraph objects.
    """
    logging.info(f"Reading clusters from {filepath}...")

    # Step 1: Collect all nodes per cluster ID
    cluster_members = defaultdict(list)
    with open(filepath) as f:
        csv_reader = csv.reader(f, delimiter="\t")
        for row in csv_reader:
            if not row:
                continue
            node_id_int, cluster_id_str = int(row[0]), row[1]
            cluster_members[cluster_id_str].append(node_id_int)

    # Step 2: Create IntangibleSubgraph objects with the *complete* list
    clusters = {}
    for cluster_id_str, node_list in cluster_members.items():
        clusters[cluster_id_str] = IntangibleSubgraph(node_list, cluster_id_str)

    logging.info(f"Found {len(clusters)} clusters to process.")
    return clusters


# --- Main Execution ---
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=str, required=True)
    args = parser.parse_args()

    # Setup logging
    log_file = os.path.join(args.output_dir, "run_python_mcs.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file, mode="w"), logging.StreamHandler()],
    )

    start_time = time.time()

    try:
        progress_path = os.path.join(args.output_dir, "progress_tracker.json")
        with open(progress_path, "r") as f:
            progress = json.load(f)

        files = progress["files"]

        # 1. Read Node ID mapping
        node_id_path = os.path.join(args.output_dir, files[NODE_ID_KEY])
        logging.info(f"Reading node ID mapping from {node_id_path}...")
        node_id_map = read_node_id_mapping(node_id_path)

        # 2. Read Original Graph
        edgelist_fn = progress["inputs"]["edgelist_fn"]
        G_orig = read_graph_and_add_nodes(edgelist_fn, node_id_map)

        # 3. Relabel graph to use 1-indexed integer IDs
        G = nx.relabel_nodes(G_orig, node_id_map)
        del G_orig  # Free memory

        # 4. Load clusters (from com_inp.csv)
        com_inp_path = os.path.join(args.output_dir, files[COM_INP_KEY])
        clusters = from_existing_clustering(com_inp_path)

        # 5. Calculate MCS for each cluster
        # mcs list is 0-indexed, but cluster IDs are 1-indexed
        mcs = [0] * len(clusters)

        for i, (cluster_id_str, cluster) in enumerate(clusters.items()):
            logging.info(
                f"Processing cluster {i+1}/{len(clusters)} (ID: {cluster_id_str})..."
            )
            # cluster.nodes contains the 1-indexed integer IDs
            subgraph = cluster.realize(G)

            # Check if subgraph has edges before calculating mincut
            if subgraph.m() > 0:
                mincut_result = viecut(subgraph)[-1]
            else:
                mincut_result = 0  # No edges, mincut is 0

            # cluster_id_str is 1-indexed, so convert to 0-index for list
            mcs_index = int(cluster_id_str) - 1
            mcs[mcs_index] = [mincut_result]  # Use list for writerows

        # 6. Write MCS file
        mcs_path = os.path.join(args.output_dir, files[MCS_KEY])
        logging.info(f"Writing MCS file to {mcs_path}...")
        with open(mcs_path, "w", newline="") as f:
            csv_writer = csv.writer(f, delimiter="\t")
            csv_writer.writerows(mcs)

        # 7. Update progress tracker
        progress["status"]["python_mcs"] = "completed"
        progress["status"]["cpp_graph_gen"] = "in_progress"
        with open(progress_path, "w") as f:
            json.dump(progress, f, indent=4)

        elapsed = time.time() - start_time
        logging.info(f"MCS calculation complete. Time: {elapsed:.4f}s")

    except Exception as e:
        logging.error(f"MCS calculation failed: {e}")
        logging.error(f"Traceback (most recent call last):\n{traceback.format_exc()}")
        # Re-raise to stop the bash script
        raise e


if __name__ == "__main__":
    import traceback

    main()
