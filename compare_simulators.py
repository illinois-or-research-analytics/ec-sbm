import pandas as pd
import argparse


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--compare-1', type=str, required=True)
    parser.add_argument('--compare-2', type=str, required=True)
    parser.add_argument('--output-file', type=str, required=True)
    return parser.parse_args()


args = parse_args()
comp_1_fp = args.compare_1
comp_2_fp = args.compare_2
output_fp = args.output_file

comp_1_df = pd.read_csv(comp_1_fp)
comp_2_df = pd.read_csv(comp_2_fp)

df = comp_1_df.merge(
    comp_2_df,
    suffixes=('_1', '_2'),
    how='inner',
    on=['stat', 'stat_type', 'distance_type'],
)
df = df.sort_values(['stat_type', 'distance_type', 'stat'])
df.to_csv(output_fp, index=False)
