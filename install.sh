conda create -n synnet python=3.12
conda activate synnet

conda install numpy scipy pandas 
conda install matplotlib seaborn 
conda install networkx

pip install networkit

### Uncomment if on UIUC Campus Cluster
# module load cmake/3.26.3
pip install git+https://github.com/vikramr2/python-mincut
pip install git+https://github.com/illinois-or-research-analytics/cm_pipeline
pip install typer