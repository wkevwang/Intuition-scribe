"""
Diarize audio using Resemblyzer (https://github.com/resemble-ai/Resemblyzer)

This script is adapted from demo 2 in the Resemblyzer repo.

Specify the audio segments for doctor and patient with start and end time,
connected with a dash. Add space between multiple audio segments.

E.g. --doctor_segments 3.2-5.5 10-12.1

Other arguments
* partials_n_frames: The number of frames used per prediction
* audio_embed_rate: How many times per second to make predictions
* speaker_embed_rate: How many times per second to embed the audio
    segments for each speaker

Every <frame_step> # of frames, partials_n_frames # of frames are
encoded to make a prediction. The prediction seems to be most associated
with the centre of that time interval.
"""

import argparse
import json
import os
import numpy as np

import resemblyzer
from resemblyzer import preprocess_wav, VoiceEncoder, sampling_rate
from resemblyzer.hparams import mel_window_step


def secs_per_partial(args):
    """
    Samples per partial (n frames encoded for a single prediction)
    in seconds
    """
    return args.partials_n_frames * mel_window_step / 1000


def samples_between_preidctions(args):
    """
    # of frames per partial
    """
    return int(np.round((sampling_rate / rate) / samples_per_frame))


def print_predictions(speaker_predictions, wav_splits, similarity_matrix, audio_embed_rate, freq=2):
    interval = int(audio_embed_rate / freq)
    for i in range(0, len(speaker_predictions), interval):
        midpoint_offset = (wav_splits[i].stop - wav_splits[i].start) / sampling_rate / 2
        seconds = (wav_splits[i].start / sampling_rate) + midpoint_offset
        print("{}m:{}s | Speaker: {} | Doctor Conf: {}".format(
            int(seconds / 60), round(seconds % 60, 1),
            speaker_predictions[i], similarity_matrix[0, i]))


def format_diarization(speaker_predictions, wav_splits):
    diarization = []
    for i in range(len(speaker_predictions)):
        midpoint_offset = (wav_splits[i].stop - wav_splits[i].start) / sampling_rate / 2
        seconds = (wav_splits[i].start / sampling_rate) + midpoint_offset
        speaker_prediction = speaker_predictions[i]
        diarization.append({
            "time": round(seconds, 2),
            "speaker": speaker_prediction
        })
    return diarization


def write_json(diarization, output_folder, audio_file):
    filename_prefix = os.path.splitext(os.path.basename(audio_file))[0]
    json_filename = filename_prefix + '_diarization.json'
    with open(os.path.join(output_folder, json_filename), 'w') as f:
        json.dump({"diarization": diarization}, f, indent=4)


def compute_diarization(wav, encoder, partials_n_frames, speaker_embed_rate,
                        audio_embed_rate, doctor_segments, patient_segments):
    # Set partials_n_frames (number of frames region per prediction)
    resemblyzer.voice_encoder.partials_n_frames = partials_n_frames

    # Cut some segments from each speaker as reference audio
    num_doctor_segments = len(doctor_segments)
    num_patient_segments = len(patient_segments)
    doctor_segments = [[float(time.split('-')[0]), float(time.split('-')[1])]
                        for time in doctor_segments]
    patient_segments = [[float(time.split('-')[0]), float(time.split('-')[1])]
                        for time in patient_segments]
    segments = doctor_segments + patient_segments
    speaker_names = (["Doctor"] * num_doctor_segments) + (["Patient"] * num_patient_segments)
    speaker_wavs = [wav[int(s[0] * sampling_rate):int(s[1]) * sampling_rate] for s in segments]

    # Encode the audio
    print("Encode the audio...")
    _, cont_embeds, wav_splits = encoder.embed_utterance(wav, return_partials=True, rate=audio_embed_rate)
    speaker_embeds = [encoder.embed_utterance(speaker_wav, rate=speaker_embed_rate) for speaker_wav in speaker_wavs]

    # Determine who spoke when
    similarity_dict = {name: cont_embeds @ speaker_embed for name, speaker_embed in 
                       zip(speaker_names, speaker_embeds)}
    similarity_matrix = np.array([cont_embeds @ speaker_embed for name, speaker_embed in
                                zip(speaker_names, speaker_embeds)])
    speaker_predictions_indexes = np.argmax(similarity_matrix, axis=0)
    speaker_predictions = [speaker_names[index] for index in speaker_predictions_indexes]

    return speaker_predictions, similarity_matrix, wav_splits

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio_file", type=str, required=True)
    parser.add_argument("--doctor_segments", type=str, nargs='+', required=True,)
    parser.add_argument("--patient_segments", type=str, nargs='+', required=True)
    parser.add_argument("--partials_n_frames", type=int, default=160, required=False)
    parser.add_argument("--audio_embed_rate", type=int, default=16, required=False)
    parser.add_argument("--speaker_embed_rate", type=int, default=16, required=False)
    parser.add_argument("--model_file", type=str, default="pretrained.pt", required=False)
    parser.add_argument("--output_folder", type=str, default=".", required=False)
    args = parser.parse_args()

    wav = preprocess_wav(args.audio_file)
    encoder = VoiceEncoder("cpu", model_file=args.model_file)

    speaker_predictions, similarity_matrix, wav_splits = compute_diarization(
        wav, encoder, args.partials_n_frames, args.speaker_embed_rate, args.audio_embed_rate,
        args.doctor_segments, args.patient_segments)

    # Print predictions
    print_predictions(speaker_predictions, wav_splits, similarity_matrix, args.audio_embed_rate)

    # Produce output JSON data
    diarization = format_diarization(speaker_predictions, wav_splits)
    write_json(diarization, args.output_folder, args.audio_file)
