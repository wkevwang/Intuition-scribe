"""
Diarize audio using Resemblyzer (https://github.com/resemble-ai/Resemblyzer)

This script is adapted from demo 2 in the Resemblyzer repo.

Specify the audio segments for doctor and patient with start and end time,
connected with a dash. Add space between multiple audio segments.

E.g. --doctor_segments 3.2-5.5 10-12.1

Other arguments
* partials_n_frames: The number of frames used per prediction. 120 seems to be the most accurate
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


def print_predictions(speaker_predictions, wav_splits, doctor_conf, patient_conf, audio_embed_rate, freq=2):
    interval = int(audio_embed_rate / freq)
    for i in range(0, len(speaker_predictions), interval):
        midpoint_offset = (wav_splits[i].stop - wav_splits[i].start) / sampling_rate / 2
        seconds = (wav_splits[i].start / sampling_rate) + midpoint_offset
        print("{}m:{}s | Speaker: {} | Doctor Conf: {} | Patient Conf: {}".format(
            int(seconds / 60), round(seconds % 60, 1),
            speaker_predictions[i],
            round(doctor_conf[i], 3),
            round(patient_conf[i], 3)))


def format_diarization(speaker_predictions, doctor_conf, patient_conf, wav_splits):
    diarization = []
    for i in range(len(speaker_predictions)):
        midpoint_offset = (wav_splits[i].stop - wav_splits[i].start) / sampling_rate / 2
        seconds = (wav_splits[i].start / sampling_rate) + midpoint_offset
        speaker_prediction = speaker_predictions[i]
        diarization.append({
            "time": round(seconds, 2),
            "speaker": speaker_prediction,
            "doctor_conf": round(doctor_conf[i], 3),
            "patient_conf": round(patient_conf[i], 3),
        })
    return diarization


def write_json(diarization, output_folder, audio_file, doctor_segments, patient_segments):
    filename_prefix = os.path.splitext(os.path.basename(audio_file))[0]
    json_filename = filename_prefix + '_diarization.json'
    with open(os.path.join(output_folder, json_filename), 'w') as f:
        json.dump({
            "diarization": diarization,
            "doctor_segments": doctor_segments,
            "patient_segments": patient_segments,
        }, f, indent=4)


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


def calculate_avg_speaker_conf(num_doctor_recs, num_patient_recs, similarity_matrix):
    assert (num_doctor_recs + num_patient_recs) == len(similarity_matrix)
    doctor_conf_matrix = similarity_matrix[:num_doctor_recs]
    patient_conf_matrix = similarity_matrix[num_doctor_recs:]
    doctor_conf = np.average(doctor_conf_matrix, axis=0).tolist()
    patient_conf = np.average(patient_conf_matrix, axis=0).tolist()
    return doctor_conf, patient_conf


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

    # Calculate speaker confidences from averaging
    doctor_conf, patient_conf = calculate_avg_speaker_conf(
        len(args.doctor_segments), len(args.patient_segments), similarity_matrix)

    # Print predictions
    print_predictions(speaker_predictions, wav_splits, doctor_conf, patient_conf, 
        args.audio_embed_rate)

    # Produce output JSON data
    diarization = format_diarization(speaker_predictions, doctor_conf, patient_conf, wav_splits)
    write_json(diarization, args.output_folder, args.audio_file, args.doctor_segments, args.patient_segments)
