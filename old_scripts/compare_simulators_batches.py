from pathlib import Path
import pandas as pd
from functools import reduce

COMP_FN = 'compare_output.csv'

names = ['abcdmcs', 'abcd']

roots = [
    Path('data/networks/abcdta4/leiden_cpm_cm'),
    Path('data/networks/abcd/leiden_cpm_cm')
]

output_dir = Path(f'output')
output_dir.mkdir(exist_ok=True, parents=True)

# Expected structure:
# root
# ├── {network_id}
# │   ├── leiden{resolution}
# │   │   ├── {replicate_id}
# │   │   │   └── {COMP_FN}

# Expected format of {COMP_FN}:
# stat,stat_type,distance_type,distance

# Output format: {output_dir}/{network_id}_{resolution}.csv
# stat,stat_type,distance_type,distance_count_{name},distance_mean_{name},distance_std_{name} for name in names
# for every (network, clustering) pair where there are at least two simulators producing at least one replicate each

network_ids = [
    set(x.name for x in root.iterdir())
    for root in roots
]

all_network_ids = reduce(
    lambda x, y: x | y,
    network_ids,
)

all_resolutions = dict()
for network_id in all_network_ids:
    resolutions = [
        set(
            x.name.replace('leiden', '')
            for x in (root / network_id).iterdir()
        )
        if (root / network_id).exists()
        else set()
        for root in roots
    ]

    all_resolutions[network_id] = reduce(
        lambda x, y: x | y,
        resolutions,
    )

all_replicates = dict()
for network_id in all_network_ids:
    all_replicates[network_id] = dict()
    for resolution in all_resolutions[network_id]:
        replicate_ids = [
            set(
                x.name
                for x in (root / network_id / f'leiden{resolution}').iterdir()
            )
            if (root / network_id / f'leiden{resolution}').exists()
            else set()
            for root in roots
        ]

        all_replicates[network_id][resolution] = reduce(
            lambda x, y: x | y,
            replicate_ids,
        )


comp_results = dict()
all_successes = dict()
one_successes = dict()

for network_id in all_network_ids:
    all_successes[network_id] = dict()
    one_successes[network_id] = dict()
    comp_results[network_id] = dict()

    for resolution in all_resolutions[network_id]:
        all_successes[network_id][resolution] = []
        one_successes[network_id][resolution] = []
        comp_results[network_id][resolution] = []

        for root in roots:
            all_success = True
            one_success = False
            comp = []

            df = None
            for replicate_id in all_replicates[network_id][resolution]:
                comp_fp = root / network_id / \
                    f'leiden{resolution}' / replicate_id / COMP_FN

                if not comp_fp.exists():
                    all_success = False
                    continue

                one_success = True

                df_tmp = pd.read_csv(comp_fp)
                df_tmp['source'] = replicate_id

                if df is None:
                    df = df_tmp
                else:
                    df = pd.concat([df, df_tmp])

            all_successes[network_id][resolution].append(all_success)
            one_successes[network_id][resolution].append(one_success)
            comp_results[network_id][resolution].append(df)

comparable_pairs = {
    (network_id, resolution)
    for network_id in all_network_ids
    for resolution in all_resolutions[network_id]
    if sum(one_successes[network_id][resolution]) > 1
}

for network_id, resolution in comparable_pairs:
    dfs = comp_results[network_id][resolution]
    agg_df = None
    for name, df in zip(names, dfs):
        grouped_df = df.groupby([
            'stat',
            'stat_type',
            'distance_type',
        ]).agg({
            'distance': ['count', 'mean', 'std'],
        })

        grouped_df.columns = grouped_df.columns.map('_'.join)
        grouped_df = grouped_df.reset_index()
        grouped_df = grouped_df.rename(columns={
            'distance_count': f'distance_count_{name}',
            'distance_mean': f'distance_mean_{name}',
            'distance_std': f'distance_std_{name}',
        })

        if agg_df is None:
            agg_df = grouped_df
        else:
            agg_df = pd.merge(
                agg_df,
                grouped_df,
                on=['stat', 'stat_type', 'distance_type'],
            )

    print(f'{network_id} {resolution}')
    agg_df.to_csv(output_dir / f'{network_id}_{resolution}.csv', index=False)
