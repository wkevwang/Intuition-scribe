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


def parse_transcript_elements(transcript_file):
    transcript_monologues = transcript_file["monologues"]
    transcript_elements_lists = [m["elements"] for m in transcript_monologues]
    transcript_elements = []
    for elements_list in transcript_elements_lists:
        for element in elements_list:
            if element['value'] == ' ':
                continue
            transcript_elements.append(element)
    return transcript_elements


def diarize_transcript_elements(transcript_elements, diarization, diarization_offset=0.0):
    """
    Add speaker label to elements in transcript_elements
    (i.e. speaker: 'Doctor' or speaker: 'Patient')

    Finds the elements in transcript_elements with start_time <= prediction_time <= end_time,
    prediction time being the timestamps with speaker labels in 'diarization'.

    Use diarization_offset to shift prediction_time by a constant.
    """
    last_speaker = 'Doctor'
    for idx, element in enumerate(transcript_elements):
        if "ts" not in element:
            # Punctuation has no time marking in transcript
            element["speaker"] = last_speaker
            continue
        start_time = float(element["ts"])
        end_time = float(element["end_ts"])
        speaker_counts = {}
        for prediction in diarization:
            prediction_time = prediction["time"] + diarization_offset
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
    return transcript_elements


def assign_no_to_patient(transcript_elements):
    """
    Assign all utterances of "No." spoken by the doctor to the patient instead
    because "No." is often not diarized correctly.
    """
    for idx, element in enumerate(transcript_elements):
        # At 2nd last index, stop
        if idx + 1 == (len(transcript_elements) - 1):
            break
        next_element = transcript_elements[idx + 1]
        if element["value"] == "No" and next_element["value"] == ".":
            element["speaker"] = "Patient"
            next_element["speaker"] = "Patient"


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio_file", type=str, required=True)
    parser.add_argument("--transcript_file", type=str, required=True)
    parser.add_argument("--diarization_file", type=str, required=True)
    parser.add_argument("--output_folder", type=str, required=True)
    parser.add_argument("--diarization_offset", required=False, type=float, default=0.0)
    parser.add_argument("--print_transcript", required=False, action='store_true', default=False)
    args = parser.parse_args()

    with open(args.transcript_file, 'r') as f:
        transcript_file = json.load(f)

    with open(args.diarization_file, 'r') as f:
        diarization_file = json.load(f)

    transcript = []

    transcript_elements = parse_transcript_elements(transcript_file)
    
    # Add speaker: "Doctor" or speaker: "Patient" labels to the list of elements
    diarize_transcript_elements(
        transcript_elements,
        diarization_file["diarization"],
        args.diarization_offset)
    
    # Assign "No." to patient
    assign_no_to_patient(transcript_elements)

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

    if args.print_transcript:
        print()
        print("TRANSCRIPT WITH PROBABILITIES")
        for turn in transcript:
            print("{}: ".format(turn['speaker']), end='')
            for item in turn['items']:
                confidence = item.get('confidence', 0)
                print_conf(item['content'], float(confidence), newline=False)
            print()
            print()
    
    filename_prefix = os.path.splitext(os.path.basename(args.audio_file))[0]
    filename = filename_prefix + '_rev_transcript_diarized.json'
    with open(os.path.join(args.output_folder, filename), 'w') as f:
        json.dump({'transcript': transcript}, f, indent=4)
