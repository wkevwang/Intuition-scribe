"""
Converts a folder of CSVs with columns for question, answer, and summary
into the format for few-shot tuning a language model
"""

import argparse
import os
import glob
import pandas as pd


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, required=True)
    args = parser.parse_args()

    all_files = glob.glob(os.path.join(args.data, '*.csv'))

    li = []
    for filename in all_files:
        df = pd.read_csv(filename, header=0)
        li.append(df)

    frame = pd.concat(li, axis=0, ignore_index=True)
    for idx, row in frame.iterrows():
        if 'no.' in row['Answer'].lower():
            print("Question: {}".format(row['Question']))
            print("Answer: {}".format(row['Answer']))
            print("Summary: {}".format(row['Summary']))