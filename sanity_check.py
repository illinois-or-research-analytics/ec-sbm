import glob
import pandas as pd


def check_wellconnected(root: str):
    # Find all files connectivity.log in directory
    files = glob.glob(root + '/**/connectivity.log', recursive=True)

    # Read csv file to see the line with "well_connected_ratio" and check if it is 1.0
    for file in files:
        with open(file, 'r') as f:
            for line in f:
                if "well_connected" in line:
                    _, ratio = line.split(',')
                    if float(ratio) < 1.0:
                        print(f"File {file} is not well connected")


def check_connected(root: str):
    # Find all files connectivity.log in directory
    files = glob.glob(root + '/**/connectivity.log', recursive=True)

    # Read csv file to see the line with "disconnected_percentage" and check if it is 0.0
    for file in files:
        with open(file, 'r') as f:
            for line in f:
                if "disconnected_percentage" in line:
                    _, perc = line.split(',')
                    if float(perc) > 0.0:
                        print(f"File {file} has disconnected clusters")


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
    # check_input_mcs,
]

root = 'data/networks/abcdta4/leiden_cpm_cm'
for test in tests:
    test(root)
