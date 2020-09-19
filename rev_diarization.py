"""
Parses the results from Rev.ai and combines
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

    transcript_monologues = transcript_file["monologues"]
    transcript_elements_lists = [m["elements"] for m in transcript_monologues]
    transcript_elements = []
    for elements_list in transcript_elements_lists:
        for element in elements_list:
            if element['value'] == ' ':
                continue
            transcript_elements.append(element)
    
    # Add speaker info to elements
    last_speaker = 'Doctor'
    for idx, element in enumerate(transcript_elements):
        if "ts" not in element:
            # Punctuation has no time marking in transcript
            element["speaker"] = last_speaker
            continue
        start_time = float(element["ts"])
        end_time = float(element["end_ts"])
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
            element["speaker"] = last_speaker # Use last speaker for now
        else:
            speaker = max(speaker_counts, key=speaker_counts.get)
            element["speaker"] = speaker
            last_speaker = speaker

    # Group speakers elements into transcript
    last_speaker = None
    for idx, element in enumerate(transcript_elements):
        speaker = element["speaker"]
        text = element["value"]
        element['content'] = text
        if last_speaker == speaker:
            if text in [',', '.', '!', '?']:
                transcript[-1]['text'] += text
            else:
                transcript[-1]['text'] += ' ' + text
            transcript[-1]['items'].append(element)
        else:
            transcript.append({
                'speaker': speaker,
                'text': text,
                'items': [element],
            })
            last_speaker = speaker

    print()
    print("TRANSCRIPT WITH PROBABILITIES")
    for turn in transcript:
        print("{}: ".format(turn['speaker']), end='')
        for item in turn['items']:
            confidence = item.get('confidence', 0)
            print_conf(item['content'], float(confidence), newline=False)
        print()
        print()
    
    filename_prefix = os.path.splitext(os.path.basename(args.transcript_file))[0]
    filename = filename_prefix + '_rev_transcript.json'
    transcript_json = {
        'transcript': transcript
    }
    with open(os.path.join(args.output_folder, filename), 'w') as f:
        json.dump(transcript_json, f, indent=4)
