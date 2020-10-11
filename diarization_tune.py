import argparse
import json
import os
import numpy as np
from copy import deepcopy

import resemblyzer
from resemblyzer import preprocess_wav, VoiceEncoder, sampling_rate
from rev_diarization import diarize_transcript_elements, parse_transcript_elements

parser = argparse.ArgumentParser()
parser.add_argument("--audio_file", type=str, required=True)
parser.add_argument("--doctor_segments", type=str, nargs='+', required=True)
parser.add_argument("--patient_segments", type=str, nargs='+', required=True)
parser.add_argument("--transcript_file", type=str, required=True)
parser.add_argument("--gt_diarization_file", type=str, required=True)
args = parser.parse_args()

with open(args.transcript_file, 'r') as f:
    transcript_file = json.load(f)
    transcript_elements = parse_transcript_elements(transcript_file)

with open(args.gt_diarization_file, 'r') as f:
    gt_diarization = json.load(f)
    gt_diarization = gt_diarization["diarization"]

wav = preprocess_wav(args.audio_file)

num_doctor_segments = len(args.doctor_segments)
num_patient_segments = len(args.patient_segments)
doctor_segments = [[float(time.split('-')[0]), float(time.split('-')[1])]
                    for time in args.doctor_segments]
patient_segments = [[float(time.split('-')[0]), float(time.split('-')[1])]
                    for time in args.patient_segments]

# Cut some segments from single speakers as reference audio
segments = doctor_segments + patient_segments
speaker_names = (["Doctor"] * num_doctor_segments) + (["Patient"] * num_patient_segments)
speaker_wavs = [wav[int(s[0] * sampling_rate):int(s[1]) * sampling_rate] for s in segments]

encoder = VoiceEncoder("cpu")

def compute_diarization(partials_n_frames, speaker_embed_rate, audio_embed_rate):
    time_per_partial_frame = partials_n_frames * 10 / 1000 * 16000
    resemblyzer.voice_encoder.partials_n_frames = partials_n_frames
    _, cont_embeds, wav_splits = encoder.embed_utterance(wav, return_partials=True, rate=audio_embed_rate)
    speaker_embeds = [encoder.embed_utterance(speaker_wav, rate=speaker_embed_rate) for speaker_wav in speaker_wavs]
    similarity_dict = {name: cont_embeds @ speaker_embed for name, speaker_embed in 
                    zip(speaker_names, speaker_embeds)}
    similarity_matrix = np.array([cont_embeds @ speaker_embed for name, speaker_embed in
                                zip(speaker_names, speaker_embeds)])
    speaker_predictions_indexes = np.argmax(similarity_matrix, axis=0)
    speaker_predictions = [speaker_names[index] for index in speaker_predictions_indexes]
    predictions = []
    # Produce output JSON data
    for i in range(len(speaker_predictions)):
        seconds = i * (960 / 16000)
        seconds += time_per_partial_frame / 2 / 16000 # Centre prediction at middle of interval
        seconds = round(seconds, 2)
        speaker_prediction = speaker_predictions[i]
        predictions.append({
            "time": seconds,
            "speaker": speaker_prediction
        })
    return predictions


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


audio_embed_rates = [8, 12, 16]
speaker_embed_rates = [8, 12, 16]
partials_n_frames_list = [115, 120, 125]

max_accuracy = 0

for audio_embed_rate in audio_embed_rates:
    for speaker_embed_rate in speaker_embed_rates:
        for partials_n_frames in partials_n_frames_list:
            pred_diarization = compute_diarization(partials_n_frames, speaker_embed_rate, audio_embed_rate)
            accuracy = diarization_word_accuracy(pred_diarization, gt_diarization, transcript_elements)
            print("Accuracy: {}% | AER: {}, SER: {}, PNF: {}".format(
                round(accuracy * 100, 2),
                audio_embed_rate,
                speaker_embed_rate,
                partials_n_frames))
            if accuracy > max_accuracy:
                print("^ New max accuracy!")
                max_accuracy = accuracy
