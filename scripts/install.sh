# conda create -n ec-sbm python=3.12
# conda activate ec-sbm

conda install numpy=1.26.4 -y
conda install pandas=2.2.3 -y
conda install networkx=3.4.2 -y
conda install -c conda-forge graph-tool=2.88 -y

pip install networkit==11.0
pip install git+https://github.com/vikramr2/python-mincut@0b2bcc64a5b939640eadc66fe0af2419d19515eb
pip install git+https://github.com/illinois-or-research-analytics/cm_pipeline@f5a0ba7b5d605af530fefa3a8a1f03fce5726495