import os
import sys
import torch

sys.path.append(os.path.dirname(os.path.abspath(__file__))) # Import current folder to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # Import parent folder to sys.path

from utils import *


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = None


def initialize_model(model_name, model_type='t5-large', checkpoints_dir='checkpoints'):
    global model
    model = initialize_t5_model(model_type)
    load_model(model, model_name, checkpoints_dir)
    model = model.to(device)


def generate_summary(question, answer, max_len=170):
    prompt = build_prompt(question, answer)
    summary = generate(model, prompt, max_len=max_len, device=device)
    return summary
