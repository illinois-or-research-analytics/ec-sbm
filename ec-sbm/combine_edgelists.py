"""Merge two edgelists (deduplicated as undirected), track provenance."""
import argparse
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline_common import standard_setup, timed


def parse_args():
    parser = argparse.ArgumentParser(
        description="Combine edgelists with undirected dedup + provenance tracking."
    )
    parser.add_argument("--edgelist-1", type=str, required=True)
    parser.add_argument("--name-1", type=str)
    parser.add_argument("--json-1", type=str)
    parser.add_argument("--edgelist-2", type=str, required=True)
    parser.add_argument("--name-2", type=str)
    parser.add_argument("--json-2", type=str)
    parser.add_argument("--output-folder", type=str, required=True)
    parser.add_argument("--output-filename", type=str, default="combined_edge.csv")
    return parser.parse_args()


def load_annotated_edgelist(edgelist_fp, name, json_fp):
    """Load edgelist CSV, label each row with its provenance.

    JSON ranges are 1-based, inclusive, over data rows only.
    """
    df = pd.read_csv(edgelist_fp, dtype=str)

    if json_fp and Path(json_fp).exists():
        with open(json_fp, "r") as f:
            mapping = json.load(f)

        prov_list = [""] * len(df)
        for source_name, (start, end) in mapping.items():
            for i in range(start - 1, end):
                if i < len(prov_list):
                    prov_list[i] = source_name
        df["prov"] = prov_list
    else:
        source_name = name if name else Path(edgelist_fp).stem
        df["prov"] = source_name

    return df


def main():
    args = parse_args()
    out_dir = standard_setup(args.output_folder)

    logging.info("--- Starting Edgelist Combination & Provenance Tracking ---")

    with timed("Combination"):
        df1 = load_annotated_edgelist(args.edgelist_1, args.name_1, args.json_1)
        df2 = load_annotated_edgelist(args.edgelist_2, args.name_2, args.json_2)

        df_combined = pd.concat([df1, df2], ignore_index=True)
        logging.info(f"Loaded {len(df_combined)} total edges prior to deduplication.")

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

        source_order = df_combined["prov"].unique()
        df_combined["prov"] = pd.Categorical(
            df_combined["prov"], categories=source_order, ordered=True
        )
        df_combined = df_combined.sort_values("prov").reset_index(drop=True)

        sources_out = {}
        current_start = 1

        for prov_name in source_order:
            count = (df_combined["prov"] == prov_name).sum()
            if count > 0:
                sources_out[prov_name] = [
                    int(current_start),
                    int(current_start + count - 1),
                ]
                current_start += count

        output_fp = out_dir / args.output_filename
        df_combined[["source", "target"]].to_csv(output_fp, index=False)

        with open(out_dir / "sources.json", "w") as f:
            json.dump(sources_out, f, indent=4)

        logging.info(f"Exported combined edgelist to {output_fp.name}")
        logging.info("Exported provenance map to sources.json")
    logging.info("--- Combination Complete ---")


if __name__ == "__main__":
    main()
