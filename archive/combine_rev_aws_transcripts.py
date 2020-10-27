"""
Patch up the low confidence parts of the Rev.ai transcipt using the
AWS Transcribe transcript, and return an edited version of the Rev.ai
transcript.
"""

import argparse
import os
import json

from rev_diarization import parse_transcript_elements as parse_rev_transcript_elements


def find_elements_in_time_bound(elements, start, end, margin=0.1):
    """
    Find the elements in "elements" that have start and end times within
    "start" and "end", with an additional margin time of "margin"

    If an element in "elements" is used, mark it as used so it is not
    used again.
    """
    elements_in_bound = []
    start_bound = start - margin
    end_bound = end + margin
    for e in elements:
        if "ts" not in e: # Skip punctuation since it does not have timestamps
            continue
        if (start_bound <= e["ts"]) and (e["end_ts"] <= end_bound) and (not e.get("used", False)):
            elements_in_bound.append(e)
            e["used"] = True
    return elements_in_bound


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio_file", type=str, required=True) # Used for getting the original filename
    parser.add_argument("--rev_transcript", type=str, required=True)
    parser.add_argument("--aws_transcript", type=str, required=True)
    parser.add_argument("--output_folder", type=str, required=True)
    args = parser.parse_args()

    with open(args.rev_transcript, 'r') as f:
        rev_transcript = json.load(f)

    with open(args.aws_transcript, 'r') as f:
        aws_transcript = json.load(f)
    
    # Form a single list of the elements for the transcript
    # Each element has "value" and for non-punct elements, "ts" and "end_ts"
    rev_transcript_elements = parse_rev_transcript_elements(rev_transcript)
    aws_transcript_items = aws_transcript["results"]["items"]
    aws_transcript_elements = []
    for item in aws_transcript_items:
        element = {
            "value": item["alternatives"][0]["content"],
        }
        if "start_time" in item:
            element["ts"] = float(item["start_time"])
            element["end_ts"] = float(item["end_time"])
            element["confidence"] = float(item["alternatives"][0]["confidence"])
        aws_transcript_elements.append(element)
    
    # Build list of final elements based on timestamps
    # Use Rev element if confidence is high. Otherwise, use AWS Transcribe element
    final_elements = []
    for rev_e in rev_transcript_elements:
        if (rev_e["type"] == "punct") or (rev_e["confidence"] > 0.95):
            final_elements.append(rev_e)
        else:
            aws_elems = find_elements_in_time_bound(
                aws_transcript_elements, rev_e["ts"], rev_e["end_ts"])
            if len(aws_elems) > 0:
                final_elements += aws_elems
            else:
                final_elements.append(rev_e)

    filename_prefix = os.path.splitext(os.path.basename(args.audio_file))[0]
    filename = filename_prefix + '_rev_aws_combined_transcript.json'
    with open(os.path.join(args.output_folder, filename), 'w') as f:
        # Write in Rev format (with a single speaker to meet the expected format)
        json.dump({
            "monologues": [{
                "speaker": 0,
                "elements": final_elements
            }]
        }, f, indent=4)
