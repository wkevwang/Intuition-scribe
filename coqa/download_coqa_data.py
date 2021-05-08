"""
Downloads CoQA dataset, formats it, and saves to disk.
"""

import argparse
from requests import get
import json
import os
import sys
import random
import csv

sys.path.append('..')
from utilities import prp

COQA_TRAIN_DATA_URL = "http://downloads.cs.stanford.edu/nlp/data/coqa/coqa-train-v1.0.json"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, required=False, default=1000)
    parser.add_argument("--data_folder", type=str, required=False, default='../data/coqa')
    args = parser.parse_args()

    json_filename = 'coqa-train-v1.0.json'
    json_file_path = os.path.join(args.data_folder, json_filename)

    if not os.path.exists(json_file_path):
        print("Downloading CoQA data...")
        with open(json_file_path, 'wb') as f:
            response = get(COQA_TRAIN_DATA_URL)
            f.write(response.content)
    
    with open(json_file_path, 'r') as f:
        data_json = json.load(f)
    
    data = []
    for passage in data_json['data']:
        for question_data, answer_data in zip(passage['questions'], passage['answers']):
            data.append({
                "question": question_data['input_text'],
                "answer": answer_data['input_text'],
            })
    
    data = list(filter(lambda d: len(d['question'].split()) > 8, data))
    data = list(filter(lambda d: len(d['answer'].split()) > 8, data))
    # data.sort(key=lambda d: len(d['answer']), reverse=True)
    random.shuffle(data)
    data = data[:args.count]

    with open(os.path.join(args.data_folder, "coqa_data.csv"), 'w') as output_file:
        writer = csv.writer(output_file)
        writer.writerow(["question", "answer"])
        for d in data:
            writer.writerow([d['question'], d['answer']])
