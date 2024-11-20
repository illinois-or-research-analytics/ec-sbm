import sys
import os
import time
import json

from utils import set_up


network_id = sys.argv[1]
resolution = sys.argv[2]
method = sys.argv[3]
based_on = sys.argv[4]

output_dir = set_up(method, based_on, network_id,
                    resolution, use_existing_clustering=True)
