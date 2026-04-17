import logging
import argparse
from pathlib import Path

import pandas as pd

from utils import setup_logging


def parse_args():
    parser = argparse.ArgumentParser(description="Clean outlier data")
    parser.add_argument(
        "--edgelist",
        type=str,
        required=True,
        help="Input network (CSV with header: source,target)",
    )
    parser.add_argument(
        "--clustering",
        type=str,
        required=True,
        help="Input clustering (CSV with header: node_id,cluster_id)",
    )
    parser.add_argument(
        "--output-folder",
        type=str,
        required=True,
        help="Output folder",
    )
    return parser.parse_args()


def remove_singleton_outliers(
    df_edges: pd.DataFrame, df_clusters: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Removes singleton clusters and filters out edges connected to them.
    """
    # 1. Find valid clusters (size > 1) to remove singletons
    cluster_counts = df_clusters["cluster_id"].value_counts()
    valid_clusters = cluster_counts[cluster_counts > 1].index

    # 2. Filter clustering dataframe to keep only nodes in valid clusters
    df_filtered_clusters = df_clusters[df_clusters["cluster_id"].isin(valid_clusters)]

    # Create a fast lookup set of the valid node IDs
    valid_nodes = set(df_filtered_clusters["node_id"])

    # 3. Filter edges: keep only if BOTH source and target are valid
    df_filtered_edges = df_edges[
        df_edges["source"].isin(valid_nodes) & df_edges["target"].isin(valid_nodes)
    ]

    return df_filtered_edges, df_filtered_clusters


def main():
    args = parse_args()
    out_dir = Path(args.output_folder)
    out_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(out_dir / "run.log")

    # Load data
    df_edges = pd.read_csv(args.edgelist)
    df_clusters = pd.read_csv(args.clustering)

    # Process data via the new dedicated function
    df_filtered_edges, df_filtered_clusters = remove_singleton_outliers(
        df_edges, df_clusters
    )

    # Save the cleaned results
    df_filtered_edges.to_csv(out_dir / "edge.csv", index=False)
    df_filtered_clusters.to_csv(out_dir / "com.csv", index=False)

    # Output summary
    logging.info(f"Done! Cleaned files saved to: {out_dir}")
    logging.info(
        f"Kept {len(df_filtered_edges)} edges and {len(df_filtered_clusters)} clustered nodes."
    )


if __name__ == "__main__":
    main()
