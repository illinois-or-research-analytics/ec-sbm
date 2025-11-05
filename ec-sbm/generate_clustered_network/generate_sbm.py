import os
import csv
import json
import logging
import argparse
from collections import defaultdict
import numpy as np
import pandas as pd
import scipy.sparse as sp
import graph_tool.all as gt

# --- Constants ---
SBM_EDGE_FILE = "inter_cluster_edges.csv"


# --- Logging Setup ---
def setup_logging(log_file):
    logging.basicConfig(
        filename=log_file,
        filemode="w",
        level=logging.INFO,
        format="%(asctime)s,%(msecs)d - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s,%(msecs)d - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console.setFormatter(formatter)
    logging.getLogger("").addHandler(console)


# --- Main Function ---
def main():
    parser = argparse.ArgumentParser(description="Generate SBM inter-cluster edges.")
    parser.add_argument("-o", "--output-dir", required=True, help="Output directory")
    args = parser.parse_args()

    output_dir = args.output_dir
    log_file = os.path.join(output_dir, "run_python_sbm.log")
    setup_logging(log_file)

    progress = {}

    try:
        progress_path = os.path.join(output_dir, "progress_tracker.json")
        logging.info(f"Reading progress from {progress_path}")
        with open(progress_path, "r") as f:
            progress = json.load(f)

        progress["status"]["python_sbm"] = "running"
        with open(progress_path, "w") as f:
            json.dump(progress, f, indent=4)

        files = progress["files"]
        inputs = progress["inputs"]

        # --- Define Paths ---
        sbm_edge_path = os.path.join(output_dir, SBM_EDGE_FILE)
        remaining_deg_path = os.path.join(output_dir, files["remaining_deg"])
        remaining_probs_path = os.path.join(output_dir, files["remaining_probs"])
        com_inp_path = os.path.join(output_dir, files["com_inp"])
        com_out_path = os.path.join(output_dir, files["com_out"])

        seed = inputs["seed"]
        gt.seed_rng(seed)
        np.random.seed(seed)

        logging.info(f"Seed set to {seed}")
        logging.info(f"Loading remaining budgets...")

        # --- Load Data ---
        out_degs = pd.read_csv(remaining_deg_path, header=None)[0].values
        num_nodes = len(out_degs)

        # Load clustering (b array)
        b = np.zeros(num_nodes, dtype=int)
        with open(com_inp_path, "r") as f:
            reader = csv.reader(f, delimiter="\t")
            for node_iid_1, cluster_iid_1 in reader:
                b[int(node_iid_1) - 1] = int(cluster_iid_1) - 1  # 0-indexed

        num_clusters = b.max() + 1

        # Load remaining probs
        rows, cols, data = [], [], []
        with open(remaining_probs_path, "r") as f:
            reader = csv.reader(f, delimiter="\t")
            for c1_1, c2_1, count in reader:
                rows.append(int(c1_1) - 1)  # 0-indexed
                cols.append(int(c2_1) - 1)  # 0-indexed
                data.append(int(count))

        probs = sp.csr_matrix((data, (rows, cols)), shape=(num_clusters, num_clusters))

        logging.info(f"Data loaded: {num_nodes} nodes, {num_clusters} clusters.")

        # --- Run SBM ---
        if out_degs.sum() > 0:
            logging.info("Running graph-tool SBM generation...")
            g = gt.generate_sbm(
                b,
                probs,
                out_degs=out_degs,
                micro_ers=True,
                micro_degs=True,
                directed=False,
            )
            logging.info("SBM generation complete.")

            # Save SBM edges
            with open(sbm_edge_path, "w", newline="") as f:
                writer = csv.writer(f, delimiter="\t")
                for src, tgt in g.iter_edges():
                    writer.writerow([int(src) + 1, int(tgt) + 1])  # 1-indexed
            logging.info(f"SBM edges written to {SBM_EDGE_FILE}")

        else:
            logging.warning("Sum of remaining degrees is 0. No SBM edges to generate.")
            # Create empty file
            with open(sbm_edge_path, "w"):
                pass
            logging.info(f"Empty SBM edge file written to {SBM_EDGE_FILE}")

        # --- Save Community File ---
        # The community file is just com_inp.csv, but with 2 columns
        logging.info(f"Writing final community file to {files['com_out']}...")
        df = pd.read_csv(
            com_inp_path, sep="\t", header=None, names=["node_id", "cluster_id"]
        )
        df.to_csv(com_out_path, sep="\t", index=False, header=False)

        # --- Update Progress ---
        progress["status"]["python_sbm"] = "completed"
        progress["files"]["sbm_edge_file"] = SBM_EDGE_FILE  # Add this key
        with open(progress_path, "w") as f:
            json.dump(progress, f, indent=4)

    except Exception as e:
        logging.error(f"Python SBM script failed: {e}")
        logging.error("Traceback:", exc_info=True)
        progress["status"]["python_sbm"] = "failed"
        if progress_path:  # Check if progress_path was loaded
            with open(progress_path, "w") as f:
                json.dump(progress, f, indent=4)
        raise e


if __name__ == "__main__":
    main()
