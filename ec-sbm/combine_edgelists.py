import argparse
import logging
import time
import json
from pathlib import Path

import pandas as pd
import numpy as np

from utils import setup_logging


def parse_args():
    parser = argparse.ArgumentParser(
        description="Combine edgelists with undirected deduplication and provenance tracking."
    )

    parser.add_argument(
        "--edgelist-1",
        type=str,
        required=True,
        help="First edgelist (CSV with source,target)",
    )
    parser.add_argument(
        "--name-1", type=str, help="Source name for edgelist 1 (if no JSON is provided)"
    )
    parser.add_argument(
        "--json-1", type=str, help="Path to sources.json for edgelist 1"
    )

    parser.add_argument(
        "--edgelist-2",
        type=str,
        required=True,
        help="Second edgelist (CSV with source,target)",
    )
    parser.add_argument(
        "--name-2", type=str, help="Source name for edgelist 2 (if no JSON is provided)"
    )
    parser.add_argument(
        "--json-2", type=str, help="Path to sources.json for edgelist 2"
    )

    parser.add_argument(
        "--output-folder", type=str, required=True, help="Output folder"
    )
    parser.add_argument(
        "--output-filename",
        type=str,
        default="combined_edge.csv",
        help="Name of the output edgelist",
    )
    return parser.parse_args()


def load_annotated_edgelist(edgelist_fp, name, json_fp):
    """Loads an edgelist and annotates each row with its source/provenance."""
    df = pd.read_csv(edgelist_fp, dtype=str)

    # If a JSON exists, unpack the exact source of each line
    if json_fp and Path(json_fp).exists():
        with open(json_fp, "r") as f:
            mapping = json.load(f)

        prov_list = [""] * len(df)
        for source_name, (start, end) in mapping.items():
            # JSON indices are 1-based (data rows only, ignoring header)
            for i in range(start - 1, end):
                if i < len(prov_list):
                    prov_list[i] = source_name
        df["prov"] = prov_list
    else:
        # Fallback to the provided generic name (or filename)
        source_name = name if name else Path(edgelist_fp).stem
        df["prov"] = source_name

    return df


def main():
    args = parse_args()
    out_dir = Path(args.output_folder)
    out_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(out_dir / "run.log")

    logging.info("--- Starting Edgelist Combination & Provenance Tracking ---")
    start = time.perf_counter()

    # 1. Load and annotate dataframes
    df1 = load_annotated_edgelist(args.edgelist_1, args.name_1, args.json_1)
    df2 = load_annotated_edgelist(args.edgelist_2, args.name_2, args.json_2)

    # 2. Combine into a single dataframe
    df_combined = pd.concat([df1, df2], ignore_index=True)
    logging.info(f"Loaded {len(df_combined)} total edges prior to deduplication.")

    # 3. Strict Undirected Deduplication
    # We logically align (A,B) and (B,A) using numpy to identify undirected duplicates
    # without permanently mutating the original order of the pairs in the final output.
    u = np.where(
        df_combined["source"] < df_combined["target"],
        df_combined["source"],
        df_combined["target"],
    )
    v = np.where(
        df_combined["source"] > df_combined["target"],
        df_combined["source"],
        df_combined["target"],
    )

    df_combined["u"] = u
    df_combined["v"] = v
    df_combined = df_combined.drop_duplicates(subset=["u", "v"], keep="first").drop(
        columns=["u", "v"]
    )

    logging.info(f"Retained {len(df_combined)} unique undirected edges.")

    # 4. Sort into contiguous blocks by provenance
    # We use a Categorical type to maintain the exact chronological order of the stages
    source_order = df_combined["prov"].unique()
    df_combined["prov"] = pd.Categorical(
        df_combined["prov"], categories=source_order, ordered=True
    )
    df_combined = df_combined.sort_values("prov").reset_index(drop=True)

    # 5. Calculate new start and end lines for the JSON
    sources_out = {}
    current_start = 1

    for prov_name in source_order:
        count = (df_combined["prov"] == prov_name).sum()
        if count > 0:
            # Note: Lines are 1-indexed, relative to the data rows (ignoring header)
            sources_out[prov_name] = [
                int(current_start),
                int(current_start + count - 1),
            ]
            current_start += count

    # 6. Export Edge CSV and Sources JSON
    output_fp = out_dir / args.output_filename
    df_combined[["source", "target"]].to_csv(output_fp, index=False)

    with open(out_dir / "sources.json", "w") as f:
        json.dump(sources_out, f, indent=4)

    logging.info(f"Exported combined edgelist to {output_fp.name}")
    logging.info(f"Exported provenance map to sources.json")
    logging.info(f"Process completed in {time.perf_counter() - start:.4f}s")
    logging.info("--- Combination Complete ---")


if __name__ == "__main__":
    main()
