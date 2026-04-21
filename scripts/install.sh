# conda create -n ec-sbm python=3.12
# conda activate ec-sbm

conda install numpy pandas scipy -y
conda install -c conda-forge graph-tool -y

pip install git+https://github.com/vikramr2/python-mincut
