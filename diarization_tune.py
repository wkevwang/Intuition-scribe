"""
Parameter sweep over
* audio_embed_rates
* speaker_embed_rates
* partials_n_frames_list
to find the highest diarization word-level accuracy.
"""

import argparse
import json
import os
import numpy as np
from copy import deepcopy

import resemblyzer
from resemblyzer import preprocess_wav, VoiceEncoder, sampling_rate

from diarization import compute_diarization, format_diarization
from rev_diarization import diarize_transcript_elements, parse_transcript_elements

def diarization_word_accuracy(pred_diarization, gt_diarization, transcript_elements):
    gt_diarization = gt_diarization[:len(pred_diarization)]
    num_correct = 0
    pred_transcript_elements = diarize_transcript_elements(deepcopy(transcript_elements), pred_diarization)
    gt_transcript_elements = diarize_transcript_elements(deepcopy(transcript_elements), gt_diarization)
    for i in range(len(pred_transcript_elements)):
        if "ts" in pred_transcript_elements[i]:
            assert pred_transcript_elements[i]["ts"] == gt_transcript_elements[i]["ts"]
        if pred_transcript_elements[i]["speaker"] == gt_transcript_elements[i]["speaker"]:
            num_correct += 1
    return num_correct / len(transcript_elements)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio_file", type=str, required=True)
    parser.add_argument("--doctor_segments", type=str, nargs='+', required=True)
    parser.add_argument("--patient_segments", type=str, nargs='+', required=True)
    parser.add_argument("--transcript_file", type=str, required=True)
    parser.add_argument("--gt_diarization_file", type=str, required=True)
    parser.add_argument("--model_file", type=str, default="pretrained.pt", required=False)
    args = parser.parse_args()

    with open(args.transcript_file, 'r') as f:
        transcript_file = json.load(f)
        transcript_elements = parse_transcript_elements(transcript_file)

    with open(args.gt_diarization_file, 'r') as f:
        gt_diarization = json.load(f)
        gt_diarization = gt_diarization["diarization"]

    wav = preprocess_wav(args.audio_file)
    encoder = VoiceEncoder("cpu", model_file=args.model_file)

    audio_embed_rates = [8, 12, 16]
    speaker_embed_rates = [8, 12, 16]
    partials_n_frames_list = [115, 120, 125]

    max_accuracy = 0

    for audio_embed_rate in audio_embed_rates:
        for speaker_embed_rate in speaker_embed_rates:
            for partials_n_frames in partials_n_frames_list:
                speaker_predictions, _, wav_splits = compute_diarization(
                    wav, encoder, partials_n_frames, speaker_embed_rate, audio_embed_rate,
                    args.doctor_segments, args.patient_segments)
                pred_diarization = format_diarization(speaker_predictions, wav_splits, args)
                accuracy = diarization_word_accuracy(pred_diarization, gt_diarization, transcript_elements)
                print("Accuracy: {}% | AER: {}, SER: {}, PNF: {}".format(
                    round(accuracy * 100, 2),
                    audio_embed_rate,
                    speaker_embed_rate,
                    partials_n_frames))
                if accuracy > max_accuracy:
                    print("^ New max accuracy!")
                    max_accuracy = accuracy
