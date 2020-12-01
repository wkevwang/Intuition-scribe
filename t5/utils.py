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
