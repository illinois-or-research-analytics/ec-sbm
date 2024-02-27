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

To run cluster-statistics:
