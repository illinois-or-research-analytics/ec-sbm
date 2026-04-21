# Installation

Python deps: `pandas`, `scipy`, `graph-tool`, `numpy`, `pymincut`.

```bash
conda create -n ec-sbm numpy pandas scipy
conda activate ec-sbm
conda install -c conda-forge graph-tool
pip install git+https://github.com/vikramr2/python-mincut
```

`pymincut` is built from source. Requires a C++ toolchain, `openmpi`, and **`cmake >= 3.2` and `< 4.0`**.
