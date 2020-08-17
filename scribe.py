"""
Parses patient-doctor conversation and generates admission note
"""

import argparse
import os
import json
import regex as re
from utilities import *
from constants import *
import snomed
from collections import OrderedDict


def find_first_sentence_response_to_question(next_turn, start_index=0):
    pattern = re.compile(r"(?:^|\. |\? |\! )([^\.\?\!]+?\.)")
    match = pattern.search(next_turn['text'], pos=start_index)
    return match


def find_qa_label_in_list_format(list_format):
    for token in list_format:
        for label in token['labels']:
            if label['type'] == "QUESTION_RESPONSE":
                return label
    return None


def qa_is_important(question_list_format, response_list_format):
    for token in question_list_format:
        for label in token['labels']:
            if not (label['type'] == "REGEX" and label['category'] == "QUESTION"):
                return True
    for token in response_list_format:
        for label in token['labels']:
            if label['type'] != "QUESTION_RESPONSE":
                return True
    return False


def determine_category_of_qa(question_list_format, response_list_format, first, pmh_mentioned):
    if first:
        return "Chief Complaint"
    if ((list_format_contains_type(question_list_format, "REGEX", "ALLERGIES_CATEGORY")) or
        (list_format_contains_type(response_list_format, "REGEX", "ALLERGIES_CATEGORY"))):
        return "Allergies"
    if ((list_format_contains_type(question_list_format, "SNOMED_CT", "products")) or
        (list_format_contains_type(response_list_format, "SNOMED_CT", "products"))):
        return "Medications"
    if ((list_format_contains_type(question_list_format, "REGEX", "FH_CATEGORY")) or
        (list_format_contains_type(response_list_format, "REGEX", "FH_CATEGORY"))):
        return "Family History"
    if ((list_format_contains_type(question_list_format, "REGEX", "SH_CATEGORY")) or
        (list_format_contains_type(response_list_format, "REGEX", "SH_CATEGORY"))):
        return "Social History"
    if ((list_format_contains_type(question_list_format, "REGEX", "PSH_CATEGORY")) or
        (list_format_contains_type(response_list_format, "REGEX", "PSH_CATEGORY"))):
        return "Past Surgical History"
    if ((list_format_contains_type(question_list_format, "REGEX", "PMH_CATEGORY")) or
        (list_format_contains_type(response_list_format, "REGEX", "PMH_CATEGORY"))):
        return "Past Medical History"
    else:
        if pmh_mentioned:
            return "Past Medical History"
        else:
            return "History of Present Illness"


def summarize_qa(question, response):
    return question + " " + response


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--terms_folder", type=str, required=True)
    parser.add_argument("--transcript", type=str, required=True)
    parser.add_argument("--print_transcript", action='store_true', required=False)
    parser.add_argument("--print_qa", action='store_true', required=False)
    parser.add_argument("--print_summary", action='store_true', required=False)
    args = parser.parse_args()

    terms = snomed.load_snomed_terms(args.terms_folder)

    with open(args.transcript, 'r') as f:
        transcript = json.load(f)

    # Add list format info to transcript
    new_transcript = []
    for turn in transcript['transcript']:
        turn['list_format'] = string_to_list_format(turn['text'])
        new_transcript.append(turn)
    transcript = new_transcript

    label_id = 0

    # REGEX
    for turn_idx, turn in enumerate(transcript):
        for marker_category, marker_regexes_list in REGEX_MARKERS.items():
            for marker_regex in marker_regexes_list:
                matches = list(re.finditer(marker_regex, turn['text'], re.IGNORECASE, overlapped=True))
                if len(matches) == 0:
                    continue
                for match_idx, match in enumerate(matches):
                    match_text = match.groups()[0]
                    # Need to manually find start/end indexes since match.span returns span of full match (including non-capturing groups)
                    start_index = turn['text'].lower().find(match_text.lower(), match.span()[0]) 
                    end_index = start_index + len(match_text)
                    label = {
                        "label_id": label_id,
                        "type": "REGEX",
                        "match": match_text,
                        "category": marker_category,
                    }
                    label_id += 1
                    add_label_to_items(turn['list_format'], label, start_index, end_index)

                    # If doctor asked a question, find the response (next statement by patient)
                    if ((marker_category == "QUESTION") and 
                        (turn['speaker'] == 'Doctor') and
                        (match_idx == len(matches) - 1) and # Select last question if there are multiple
                        (turn_idx < len(transcript) - 1)): # Make sure there's another turn after
                        next_turn = transcript[turn_idx + 1]
                        response_text = next_turn["text"]
                        response_label = {
                            "label_id": label_id,
                            "type": "QUESTION_RESPONSE",
                            "question_label_id": label['label_id'],
                            "question": match_text,
                            "response": response_text,
                            "category": None,
                        }
                        label_id += 1
                        add_label_to_items(next_turn['list_format'], response_label, 0, len(response_text))

    # SNOMED CT
    for turn in transcript:
        for term_category, terms_list in terms.items():
            for term in terms_list:
                if match_full_term(term, turn['text']):
                    label = {
                        "label_id": label_id,
                        "type": "SNOMED_CT",
                        "term": term,
                        "category": term_category
                    }
                    label_id += 1
                    start_index = turn['text'].lower().find(term.lower())
                    end_index = start_index + len(term)
                    add_label_to_items(turn['list_format'], label, start_index, end_index)

    # Print labelled transcript
    if args.print_transcript:
        for turn in transcript:
            coloured_text = list_format_to_coloured_string(turn['list_format'])
            print("{}: {}".format(turn['speaker'], coloured_text))
            print()
        print()

    note = {category: [] for category in CATEGORIES}

    # Build Q&A pairs
    qa_summaries = []
    first = True
    pmh_mentioned = False
    for turn in transcript:
        qa_label = find_qa_label_in_list_format(turn['list_format'])
        if qa_label:
            question = qa_label['question']
            response = qa_label['response']
            question_list_format = find_list_format_slice_with_label_id(transcript, qa_label['question_label_id'])
            response_list_format = find_list_format_slice_with_label_id(transcript, qa_label['label_id'])
            qa_is_important_ = qa_is_important(question_list_format, response_list_format)
            if qa_is_important_:
                qa_summary = summarize_qa(question, response)
                category = determine_category_of_qa(question_list_format, response_list_format, first, pmh_mentioned)
                qa_summaries.append({
                    "text": qa_summary,
                    "category": category,
                })
                note[category].append(qa_summary)
                first = False
                if category == "Past Medical History":
                    pmh_mentioned = True
            if args.print_qa:
                print("Question: {}".format(question))
                print("Response: {}".format(response))
                if qa_is_important_:
                    print("QA is important")
                    print(category)
                print()
    print()

    # Print summary
    if args.print_summary:
        for category in CATEGORIES:
            print(category.upper())
            for sentence in note[category]:
                print(sentence, end=' ')
            if len(note[category]) == 0:
                print("None")
            else:
                print()
            print()
