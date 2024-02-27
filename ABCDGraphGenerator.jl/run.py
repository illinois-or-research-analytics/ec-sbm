seed = 0

# Number of nodes
n = 10

# Degree distribution
t1 = 2
d_min = 1
d_max = 2

# Community size distribution
t2 = 3
c_min = 3
c_max = 10

# Mixing parameter
xi = 0.5

with open('config.toml', 'w') as f:
    f.write(f'''seed = "{seed}"
n = "{n}"
t1 = "{t1}"
d_min = "{d_min}"
d_max = "{d_max}"
d_max_iter = "1000"
t2 = "{t2}"
c_min = "3"
c_max = "4"
c_max_iter = "1000"
xi = "0.2"
islocal = "false"
isCL = "false"
degreefile = "sample/deg.dat"
communitysizesfile = "sample/cs.dat"
communityfile = "sample/com.dat"
networkfile = "sample/edge.dat"
nout = "0"''')
