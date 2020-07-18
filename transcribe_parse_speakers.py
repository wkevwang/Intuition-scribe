"""
Parses the results from Amazon Transcribe Medical and returns
a transcript with individual speakers.
"""

import argparse
import json
import re
import os


def get_text_of_speaker_segment(speaker_segment):
    for segment in segments:
        if ((segment['start_time'] == speaker_segment['start_time']) and
            (segment['end_time'] == speaker_segment['end_time'])):
            if len(segment['alternatives']) > 0:
                return segment['alternatives'][0]['transcript']
    print("Cannot find text for speaker segment:", speaker_segment)


def clean_transcript(transcript):
    punct_chars = ['.', '!', '?']
    for idx, turn in enumerate(transcript):
        last_char = turn['text'][-1]
        if last_char not in punct_chars: # If last sentence is only a partial sentence
            sentences = re.split(r'(\.|\!|\?)', turn['text'])
            if len(sentences) > 1: # If there's multiple sentences in this turn
                # Move last partial sentence to next turn's start
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
        text = get_text_of_speaker_segment(speaker_segment)
        speaker = speaker_segment['speaker_label']
        if last_speaker == speaker:
            transcript[-1]['text'] += ' ' + text
        else:
            transcript.append({
                'speaker': speaker,
                'text': text
            })
            last_speaker = speaker
                
    transcript = clean_transcript(transcript)

    for turn in transcript:
        print("{}: {}".format(turn['speaker'], turn['text']))

    with open(args.output, 'w') as outfile:
        json.dump({
            'transcript': transcript
        }, outfile, indent=4)
