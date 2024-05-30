import glob
import pandas as pd
import json
import sys


def check_wellconnected(root: str):
    files = glob.glob(root + '/**/stats.json', recursive=True)
    for file in files:
        with open(file, 'r') as f:
            data = json.load(f)
            if data['ratio_wellconnected_clusters'] < 1.0:
                print(f"File {file} is not well connected")


def check_connected(root: str):
    files = glob.glob(root + '/**/stats.json', recursive=True)
    for file in files:
        with open(file, 'r') as f:
            data = json.load(f)
            if data['n_disconnects'] > 0:
                print(f"File {file} is disconnected")


def check_output_mcs(root: str):
    # Find all files mcs.csv in directory
    files = glob.glob(root + '/**/mcs.csv', recursive=True)

    # Read each csv file to see if the "mcs_gen" is less than "mcs"
    # Use pandas
    for file in files:
        df = pd.read_csv(file)
        if (df['mcs_gen'] < df['mcs']).any():
            print(f"File {file} has mcs_gen greater than mcs")


def check_input_mcs(root: str):
    # Find all files mcs.tsv in directory
    files = glob.glob(root + '/**/mcs.tsv', recursive=True)

    # Read each file line by line to see if any line is exactly "0"
    for file in files:
        with open(file, 'r') as f:
            for line in f:
                if line.strip() == "0":
                    print(f"File {file} has 0 mcs")


tests = [
    check_wellconnected,
    check_connected,
    check_output_mcs,
    check_input_mcs,
]

root = sys.argv[1]
for test in tests:
    test(root)
