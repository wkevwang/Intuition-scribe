"""
Parses the results from Amazon Transcribe Medical and combines
it with a Resemblyzer diarization to produce a diarized transcript.
"""

import argparse
import json
import regex as re
import os
import copy
from colr import color
import sys

from utilities import *

def all_dict_values_same(d):
    return (len(set(d.values())) == 1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--transcript_file", type=str, required=True)
    parser.add_argument("--diarization_file", type=str, required=True)
    parser.add_argument("--output_folder", type=str, required=True)
    parser.add_argument("--diarization_offset", required=False, type=float, default=0.0)
    args = parser.parse_args()

    with open(args.transcript_file, 'r') as f:
        transcript_file = json.load(f)
    
    with open(args.diarization_file, 'r') as f:
        diarization_file = json.load(f)
    
    transcript = []

    transcript_items = transcript_file["results"]["items"]

    # Add speaker info to items
    last_speaker = 'Doctor'
    for idx, item in enumerate(transcript_items):
        if "start_time" not in item:
            # Punctuation has no time marking in transcript
            item["speaker"] = last_speaker
            continue
        start_time = float(item["start_time"])
        end_time = float(item["end_time"])
        speaker_counts = {}
        for prediction in diarization_file["diarization"]:
            prediction_time = prediction["time"] + args.diarization_offset
            if prediction_time > end_time:
                break
            if start_time <= prediction_time <= end_time:
                speaker_prediction = prediction["speaker"]
                if speaker_prediction in speaker_counts:
                    speaker_counts[speaker_prediction] += 1
                else:
                    speaker_counts[speaker_prediction] = 0
        # If no overlapping preds or equal count of predictions from multiple speakers
        if ((len(speaker_counts) == 0) or 
            (len(speaker_counts) > 1 and all_dict_values_same(speaker_counts))):
            item["speaker"] = last_speaker # Use last speaker for now
        else:
            speaker = max(speaker_counts, key=speaker_counts.get)
            item["speaker"] = speaker
            last_speaker = speaker

    # Group speakers items into transcript
    last_speaker = None
    for idx, item in enumerate(transcript_items):
        speaker = item["speaker"]
        alternative = item["alternatives"][0]
        text = alternative["content"]
        if last_speaker == speaker:
            if text in [',', '.', '!', '?']:
                transcript[-1]['text'] += text
            else:
                transcript[-1]['text'] += ' ' + text
            transcript[-1]['items'].append(alternative)
        else:
            transcript.append({
                'speaker': speaker,
                'text': text,
                'items': [alternative],
            })
            last_speaker = speaker

    print()
    print("TRANSCRIPT WITH PROBABILITIES")
    for turn in transcript:
        print("{}: ".format(turn['speaker']), end='')
        for item in turn['items']:
            print_conf(item['content'], float(item['confidence']), newline=False)
        print()
        print()
