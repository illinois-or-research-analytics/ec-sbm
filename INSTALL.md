# Installation

## Dependencies

Python 3.11 with:

- `graph-tool` (conda-forge)
- `pandas`, `numpy`, `scipy` (conda)
- `pymincut` (pip, from source)
- `optuna` (optional; only required for `--pso-search-strategy bayesian` in v3; secant default does not need it)

## Conda recipe

```bash
conda create -n ecsbm python=3.11 -y
conda activate ecsbm
conda install -c conda-forge graph-tool -y
conda install numpy pandas scipy -y
pip install git+https://github.com/vikramr2/python-mincut
```

`pymincut` is built from source. Requires a C++ toolchain, `openmpi`, and
**`cmake >= 3.2` and `< 4.0`**. Using CMake 4.0+ is possible by forcing the minimum-policy version:

```bash
CMAKE_ARGS="-DCMAKE_POLICY_VERSION_MINIMUM=3.5" \
    pip install git+https://github.com/vikramr2/python-mincut
```

## Sanity check

```bash
bash scripts/run_ecsbm.sh \
    --version v1 \
    --input-edgelist   examples/input/dnc/edge.csv \
    --input-clustering examples/input/dnc/com.csv \
    --output-dir       /tmp/ecsbm-sanity \
    --seed 1
sha256sum /tmp/ecsbm-sanity/edge.csv
# 42128ea4b826a7c64f59b1905ae124374741fe0feb68fa3e9c0604b2c15bc302
```
