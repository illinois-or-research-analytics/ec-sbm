Campus-Cluster:

To run LFR generator:
- module load gcc

To run ABCD generator:
- Download and install Julia:
```
curl -fsSL https://install.julialang.org | sh
```
- Set path for certificate
```
export SSL_CERT_FILE=/etc/ssl/certs/ca-bundle.crt
```
- Install
```
julia ABCDGraphGenerator.jl/utils/install.jl
```

To modify ABCD generator:
```
ln -s /home/vltanh/synnet/ABCDGraphGenerator.jl ~/.julia/packages/ABCDGraphGenerator/ZBC5x
```

To run cluster-statistics:
