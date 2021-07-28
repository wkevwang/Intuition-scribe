"""
Prints transcript with probabilities
"""

import os
import json
import argparse

from utilities import print_transcript


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--transcript_file", type=str, required=True)
    args = parser.parse_args()

    with open(args.transcript_file, 'r') as f:
        transcript_json = json.load(f)
        transcript = transcript_json["transcript"]
    
    print_transcript(transcript, show_confidence=True)
