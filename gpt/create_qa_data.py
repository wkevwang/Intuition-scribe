"""
Converts a folder of CSVs with columns for question, answer, and summary
into the format for few-shot tuning a language model
"""

import argparse
import os
import glob
import pandas as pd
import json

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, required=True)
    args = parser.parse_args()

    all_files = glob.glob(os.path.join(args.data, '*.csv'))

    li = []
    for filename in all_files:
        df = pd.read_csv(filename, header=0)
        li.append(df)

    df = pd.concat(li, axis=0, ignore_index=True)

    categories = [
        "General",
        "Social History",
        "Pain",
        "Negation",
        "Family History",
        "Severity",
        "Medication",
    ]

    data_array = {c: [] for c in categories}
    data_string = {c: "" for c in categories}

    for idx, row in df.iterrows():
        category = row['Category']
        data_array[category].append(row)

    for category, array in data_array.items():
        print("Category: {} | {} items total".format(category, len(array)))
        for row in array:
            question_str = "Question: {}\n".format(row['Question'])
            answer_str = "Answer: {}\n".format(row['Answer'])
            summary_str = "Summary: {}\n".format(row['Summary'])
            print(question_str, end='')
            print(answer_str, end='')
            print(summary_str, end='')
            data_string[category] += question_str + answer_str + summary_str
        print()
    
    with open("context.json", 'w') as output_file:
        json.dump(data_string, output_file, indent=4)
