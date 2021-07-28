import os
import sys
import torch
import csv

sys.path.append(os.path.dirname(os.path.abspath(__file__))) # Import current folder to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # Import parent folder to sys.path

from utils import *


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = None


def init_model(model_name, model_type='t5-large', checkpoints_dir='checkpoints'):
    global model
    model = initialize_t5_model(model_type)
    load_model(model, model_name, checkpoints_dir)
    model = model.to(device)


def summarize(question, answer, max_len=170):
    prompt = build_prompt(question, answer)
    summary = generate(model, prompt, max_len=max_len, device=device)
    return summary


def generate_summaries_for_csv(csv_path):
    data_list = []
    with open(csv_path ,'r') as csv_file:
        next(csv_file, None) # Skip header line (or return None is file empty)
        csv_reader = csv.reader(csv_file)
        for row in csv_reader:
            data_list.append({
                "question": row[0].strip(),
                "answer": row[1].strip(),
            })
    for data in data_list:
        summary = summarize(data['question'], data['answer'])
        data['summary'] = summary
        print("Q: {}\nA: {}\nS: {}\n".format(data['question'], data['answer'], summary))
    output_filename = os.path.splitext(csv_path)[0] + "_with_summaries.csv"
    with open(output_filename, 'w') as output_file:
        writer = csv.writer(output_file)
        writer.writerow(["question", "answer", "summary"])
        for data in data_list:
            writer.writerow([data['question'], data['answer'], data['summary']])
