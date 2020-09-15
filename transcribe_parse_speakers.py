"""
Parses the results from Amazon Transcribe Medical and returns
a transcript with individual speakers.
"""

import argparse
import json
import regex as re
import os
import copy

from utilities import *


def get_text_of_speaker_segment(speaker_segment, segments):
    for segment in segments:
        if ((segment['start_time'] == speaker_segment['start_time']) and
            (segment['end_time'] == speaker_segment['end_time'])):
            if len(segment['alternatives']) > 0:
                return segment['alternatives'][0]['transcript'], segment['alternatives'][0]['items']
    print("Cannot find text for speaker segment:", speaker_segment)


def determine_speakers(transcript):
    num_question_marks_spk_0 = sum(turn['text'].count('?') for turn in transcript if turn['speaker'] == 'spk_0')
    num_question_marks_spk_1 = sum(turn['text'].count('?') for turn in transcript if turn['speaker'] == 'spk_1')
    speaker_map = {
        "spk_0": "Doctor" if num_question_marks_spk_0 > num_question_marks_spk_1 else "Patient",
        "spk_1": "Doctor" if num_question_marks_spk_1 > num_question_marks_spk_0 else "Patient",
    }
    for turn in transcript:
        turn['speaker'] = speaker_map[turn['speaker']]
    return transcript


def move_unfinished_sentences(transcript):
    punct_chars = ['.', '!', '?']
    for idx, turn in enumerate(transcript):
        if len(turn['text']) == 0:
            continue
        last_char = turn['text'][-1]
        if last_char not in punct_chars: # If last sentence is only a partial sentence
            sentences = re.split(r'(\.|\!|\?)', turn['text'])
            if len(sentences) > 1: # If there's multiple sentences in this turn
                # Move last partial sentence to next turn's start
                if idx == len(transcript) - 1:
                    continue
                transcript[idx + 1]['text'] = (sentences[-1] + ' ' + transcript[idx + 1]['text']).strip()
                del sentences[-1]
                turn['text'] = ''.join(sentences).strip()
            else: # If there's only 1 sentence in this turn
                # Move next turn's first partial sentence to end of this turn
                if idx + 1 == len(transcript): # If there's no next turn, break
                    break
                next_turn_text = transcript[idx + 1]['text']
                if re.search(r'(\.|\!|\?)', next_turn_text) == None: # If next turn has only 1 sentence, continue
                    continue
                index_of_first_punct = min(next_turn_text.find(c) for c in punct_chars if c in next_turn_text)
                next_turn_first_sentence = next_turn_text[:(index_of_first_punct + 1)]
                turn['text'] += ' ' + next_turn_first_sentence
                transcript[idx + 1]['text'] = next_turn_text[(index_of_first_punct + 1):].strip()
    return transcript


def split_last_question(text):
    last_question_index = -1
    for idx, char in enumerate(text):
        if (last_question_index > 0) and (char in ['.', '!']):
            break
        if char == '?':
            last_question_index = idx
    if last_question_index >= 0: # If question mark found
        return text[:(last_question_index + 1)].strip(), text[(last_question_index + 1):].strip()
    else: # If not question mark found
        return text, ''


def split_last_statement(text):
    last_period_index = -1
    for idx, char in enumerate(text):
        if (last_period_index > 0) and (char == '?'):
            break
        if char in ['.', '!']:
            last_period_index = idx
    if last_period_index >= 0: # If period found
        return text[:(last_period_index + 1)].strip(), text[(last_period_index + 1):].strip()
    else: # If not question mark found
        return text, ''


def move_question_responses(transcript):
    new_transcript = []
    for turn in transcript:
        if turn['speaker'] == 'Doctor':
            current_speaker = 'Doctor'
            a, b = split_last_question(turn['text'])
            while b != '':
                new_transcript.append({
                    'speaker': current_speaker,
                    'text': a
                })
                if current_speaker == 'Patient':
                    current_speaker = 'Doctor'
                else:
                    current_speaker = 'Patient'
                if current_speaker == 'Patient':
                    a, b = split_last_statement(b)
                else:
                    a, b = split_last_question(b)
            new_transcript.append({
                'speaker': current_speaker,
                'text': a
            })
        else: # If patient
            if (len(new_transcript) > 0) and (new_transcript[-1]['speaker'] == 'Patient'):
                new_transcript[-1]['text'] += ' ' + turn['text']
            else:
                new_transcript.append(turn)
    return new_transcript


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()

    with open(args.file, 'r') as f:
        response_file = json.load(f)

    speaker_segments = response_file['results']['speaker_labels']['segments']
    segments = response_file['results']['segments']

    transcript = []
    last_speaker = None

    for speaker_segment in speaker_segments:
        text, items = get_text_of_speaker_segment(speaker_segment, segments)
        speaker = speaker_segment['speaker_label']
        if last_speaker == speaker:
            transcript[-1]['text'] += ' ' + text
            transcript[-1]['items'] += items
        else:
            transcript.append({
                'speaker': speaker,
                'text': text,
                'items': items,
            })
            last_speaker = speaker
    
    original_transcript = copy.copy(transcript)
    transcript = determine_speakers(transcript)
    transcript = move_unfinished_sentences(transcript)
    # transcript = move_question_responses(transcript)

    print("CLEANED TRANSCRIPT")
    for turn in transcript:
        print()
        print("{}: {}".format(turn['speaker'], turn['text']))

    print()
    print("ORIGINAL TRANSCRIPT WITH PROBABILITIES")
    for turn in original_transcript:
        print("{}: ".format(turn['speaker']), end='')
        for item in turn['items']:
            print_conf(item['content'], float(item['confidence']), newline=False)
        print()
        print()

    with open(args.output, 'w') as outfile:
        json.dump({
            'transcript': transcript
        }, outfile, indent=4)
