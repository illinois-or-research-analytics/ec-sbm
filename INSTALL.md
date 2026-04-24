# Installation

## Dependencies

Python 3.11 with:

- `graph-tool` (conda-forge)
- `pandas`, `numpy`, `scipy` (conda)
- `pymincut` (pip, from source)

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
# e2b5a6914b12f39c9356bbeba17a61ef82b0ce97258caf1dfef45b42d64a3d5b
```
