import os
import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer


def build_prompt(question, answer):
    prompt = "summarize: <question> {} <answer> {}".format(
        question, answer
    )
    return prompt


def generate(model, input_, max_len=128, device='cpu'):
    tokenizer = T5Tokenizer.from_pretrained('t5-base')
    input_ids = tokenizer(input_, return_tensors='pt').input_ids
    input_ids = input_ids.to(device)
    beam_outputs = model.generate(
        input_ids=input_ids,
        do_sample=True,
        max_length=max_len,
        top_k=120,
        top_p=0.7,
        early_stopping=True,
        num_return_sequences=1
    )
    # Crop out <pad> and </s> (first and last token)
    final_output = beam_outputs[0][1:-1]
    sentence = tokenizer.decode(final_output)
    return sentence


def initialize_t5_model(t5_model_type):
    """
    Initialize T5 model with size <t5_model_type>.
    """
    model = T5ForConditionalGeneration.from_pretrained(t5_model_type)
    return model


def get_checkpoint_file_path(model_name, checkpoints_dir):
    """
    Returns the full path where model should be saved.
    E.g. /home/kevin/scribe/checkpoints/model-5.pt

    The checkpoints_dir is created in the directory of this script.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    checkpoints_dir_full = os.path.join(script_dir, checkpoints_dir)
    model_file_name = model_name + '.pt'
    checkpoint_file_path = os.path.join(checkpoints_dir_full, model_file_name)
    return checkpoint_file_path


def save_model(model, model_name, checkpoints_dir):
    """
    Saves model with name <model>.pt in checkpoints_dir.
    Creates checkpoints_dir if it doesn't exist already.
    """
    checkpoint_file_path = get_checkpoint_file_path(model_name, checkpoints_dir)
    checkpoints_dir_full = os.path.dirname(checkpoint_file_path)
    os.makedirs(checkpoints_dir_full, exist_ok=True)
    torch.save(model.state_dict(), checkpoint_file_path)


def load_model(model, model_name, checkpoints_dir):
    checkpoint_file_path = get_checkpoint_file_path(model_name, checkpoints_dir)
    state_dict = torch.load(checkpoint_file_path)
    model.load_state_dict(state_dict)


def num_params_transformer(
    vocab_size,
    layers,
    d_model,
    d_ff,
    heads,
    d_attention,
):
    return (
        d_model * vocab_size + # Embedding
        (d_model * d_attention * 3 * heads) * layers + # Encoder Attention (W_Q, W_K, W_V)
        (heads * d_attention * d_model) * layers + # Encoder Concat Heads (W_O)
        (d_model * d_ff + d_ff * d_model) * layers + # Encoder Feedforward
        (d_model * d_attention * 4 * heads) * layers + # Decoder Attention (W_Q, W_K, W_V, W_Q2)
        (heads * d_attention * d_model) * layers + # Decoder Concat Heads (W_O)
        (d_model * d_ff + d_ff * d_model) * layers + # Decoder Feedforward
        d_model * vocab_size # Projection
    )