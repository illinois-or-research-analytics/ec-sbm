# Installation

## Dependencies

Python 3.10+ with:

- `graph-tool`
- `pymincut`
- `networkit`
- `powerlaw`
- `pandas`
- `numpy`
- `scipy`

## Conda recipe

```bash
conda create -n ec-sbm -c conda-forge \
    python=3.10 graph-tool networkit powerlaw pandas numpy scipy
conda activate ec-sbm
pip install git+https://github.com/vikramr2/python-mincut
```

`pymincut` is built from source. Requires a C++ toolchain, `openmpi`, and
**`cmake >= 3.2` and `< 4.0`**.

## Sanity check

```bash
bash scripts/run_ecsbm.sh \
    --version v1 \
    --input-edgelist examples/input/dnc/edge.csv \
    --input-clustering examples/input/dnc/com.csv \
    --output-dir /tmp/ecsbm-sanity \
    --seed 1
sha256sum /tmp/ecsbm-sanity/edge.csv
# e2b5a6914b12f39c9356bbeba17a61ef82b0ce97258caf1dfef45b42d64a3d5b
```
