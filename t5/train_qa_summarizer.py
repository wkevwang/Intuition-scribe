import argparse
import os
import glob
import csv
import random
from rouge_score import rouge_scorer
from sklearn.model_selection import train_test_split
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import T5Tokenizer
from transformers import Adafactor, AdamW

from utils import *

class QuestionAnswerSummaryDataset(Dataset):
    def __init__(self, mode, data_folder, input_max_length=128, test_size=0.1):
        if mode not in ["train", "validation"]:
            return ValueError("Invalid mode!")
        
        self.mode = mode
        self.data_folder = data_folder
        self.input_max_length = input_max_length
        self.test_size = test_size

        self.tokenizer = T5Tokenizer.from_pretrained('t5-base')
        self.random_seed = 42

        self.train_data = None # self.load_data will populate
        self.validation_data = None # self.load_data will populate

        self.load_data(self.data_folder)
    
    def get_data(self):
        if self.mode == "train":
            return self.train_data
        elif self.mode == "validation":
            return self.validation_data

    def is_empty_string(self, string):
        return len(string) == 0
    
    def add_punctuation_to_end_of_sentence(self, string):
        if string[-1] in ['.', '?', '!']:
            return string
        else:
            return string + '.'

    def load_data(self, data_folder):
        """
        Load data from data_folder. Expects CSV files
        with (at least) 3 columns:
            1) Question
            2) Answer
            3) Summary
        """
        data_list = []
        all_files = sorted(glob.glob(os.path.join(data_folder, '*.csv'))) # Sort to maintain order
        for filename in all_files:
            with open(filename ,'r') as csv_file:
                next(csv_file, None) # Skip header line (or return None is file empty)
                csv_reader = csv.reader(csv_file)
                for row in csv_reader:
                    # Exclude if no question, answer, or summary
                    if (self.is_empty_string(row[0]) or
                        self.is_empty_string(row[1]) or
                        self.is_empty_string(row[2])):
                        continue
                    data_list.append({
                        "question": row[0].strip(),
                        "answer": row[1].strip(),
                        "summary": self.add_punctuation_to_end_of_sentence(row[2].strip()), # Add punctuation if needed
                    })
        self.train_data, self.validation_data = train_test_split(
            data_list,
            test_size=self.test_size,
            shuffle=True,
            random_state=self.random_seed,
        )

    def __len__(self):
        return len(self.get_data())

    def __getitem__(self, idx):
        data = self.get_data()[idx]
        prompt = build_prompt(data["question"], data["answer"])
        label = data["summary"]
        prompt_data = self.tokenizer(
            prompt,
            padding="max_length",
            max_length=self.input_max_length,
            return_tensors='pt')
        label_data = self.tokenizer(
            label,
            padding="max_length",
            max_length=self.input_max_length,
            return_tensors='pt')
        return {
            "question": data["question"],
            "answer": data["answer"],
            "prompt": prompt,
            "label": label,
            "prompt_data": prompt_data,
            "label_data": label_data,
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, default="model")
    parser.add_argument("--use_cpu", action='store_true', default=False)
    parser.add_argument("--load_model", type=str, default=None)
    parser.add_argument("--checkpoints_dir", type=str, default="checkpoints")
    parser.add_argument("--qa_data", type=str, required=True)
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--num_epochs", type=int, default=5)
    parser.add_argument("--model", type=str, default="t5-small")
    parser.add_argument("--input_max_length", type=int, default=128)
    parser.add_argument("--test_size", type=float, default=0.1)
    parser.add_argument("--optimizer", type=str, default="Adam")
    args = parser.parse_args()

    print("Arguments: {}".format(args))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if args.use_cpu:
        device = 'cpu'
    print("Using device: {}".format(device))

    train_dataset = QuestionAnswerSummaryDataset(
        mode="train",
        data_folder=args.qa_data,
        input_max_length=args.input_max_length,
        test_size=args.test_size)

    train_dataloader = torch.utils.data.DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True)

    validation_dataset = QuestionAnswerSummaryDataset(
        mode="validation",
        data_folder=args.qa_data,
        input_max_length=args.input_max_length,
        test_size=args.test_size)

    validation_dataloader = torch.utils.data.DataLoader(
        validation_dataset,
        batch_size=args.batch_size)

    # Print data stats
    print("{} items in train dataset".format(len(train_dataset)))
    print("{} items in validation dataset".format(len(validation_dataset)))

    # Define the model
    model = initialize_t5_model(args.model)
    model = model.to(device)

    # Load model
    if args.load_model:
        load_model(model, args.load_model, args.checkpoints_dir)

    # Define optimizer
    if args.optimizer == "Adam":
        optimizer = torch.optim.Adam(model.parameters())
    elif args.optimizer == "AdamW":
        optimizer = AdamW(model.parameters())
    elif args.optimizer == "Adafactor":
        optimizer = Adafactor(model.parameters(), lr=1e-3, scale_parameter=False, relative_step=False, warmup_init=False)
    else:
        raise ValueError("Invalid optimizer")

    # Define ROUGE Scorer
    scorer = rouge_scorer.RougeScorer(['rouge1'])

    # Train the model
    for epoch in range(args.num_epochs):
        print("Epoch: {}".format(epoch + 1))

        model.train()
        for i, data in enumerate(train_dataloader):
            optimizer.zero_grad()
            data["prompt_data"]["input_ids"] = data["prompt_data"]["input_ids"].to(device)
            data["prompt_data"]["attention_mask"] = data["prompt_data"]["attention_mask"].to(device)
            data["label_data"]["input_ids"] = data["label_data"]["input_ids"].to(device)
            output = model(
                input_ids=data["prompt_data"]["input_ids"].squeeze(1),
                attention_mask=data["prompt_data"]["attention_mask"].squeeze(1),
                labels=data["label_data"]["input_ids"].squeeze(1),
                return_dict=True,
            )
            loss = output.loss
            loss.backward()
            optimizer.step()
            print("Train Loss: {}".format(round(loss.item(), 4)))

        print("Running validation...")
        model.eval()
        with torch.no_grad():
            total_loss = 0
            total_batches = 0
            total_rouge1_f1_score = 0
            for i, data in enumerate(validation_dataloader):
                data["prompt_data"]["input_ids"] = data["prompt_data"]["input_ids"].to(device)
                data["prompt_data"]["attention_mask"] = data["prompt_data"]["attention_mask"].to(device)
                data["label_data"]["input_ids"] = data["label_data"]["input_ids"].to(device)
                output = model(
                    input_ids=data["prompt_data"]["input_ids"].squeeze(1),
                    attention_mask=data["prompt_data"]["attention_mask"].squeeze(1),
                    labels=data["label_data"]["input_ids"].squeeze(1),
                    return_dict=True,
                )
                total_loss += output.loss.item()
                total_batches += 1

                for idx, (prompt, label) in enumerate(zip(data["prompt"], data["label"])):
                    pred_sentence = generate(model, prompt, max_len=args.input_max_length, device=device)
                    print("-----\nQ: {} | A: {}".format(data["question"][idx], data["answer"][idx]))
                    print("Summary: {}\n".format(pred_sentence))
                    total_rouge1_f1_score += scorer.score(label, pred_sentence)['rouge1'].fmeasure
            print("-----")

            print("Validation Loss: {}".format(round(total_loss / total_batches, 4)))
            print("Validation ROUGE-1 F1: {}".format(round(total_rouge1_f1_score / (total_batches * args.batch_size), 4)))

    print("Saving model...")
    save_model(model, args.model_name, args.checkpoints_dir)
