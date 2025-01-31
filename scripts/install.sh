conda create -n ec-sbm python=3.12
conda activate ec-sbm

conda install numpy=1.26.4 # networkit will scream with newer versions
conda install -c conda-forge graph-tool
conda install pandas
conda install networkx

pip install networkit
pip install git+https://github.com/vikramr2/python-mincut
pip install git+https://github.com/illinois-or-research-analytics/cm_pipeline
