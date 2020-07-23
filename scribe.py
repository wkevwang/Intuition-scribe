"""
Parses patient-doctor conversation and generates admission note
"""

import argparse
import os
import json
import re
from colorama import Fore, Style
from utilities import *


def string_to_list_format(text):
    tokens = re.split(r'( |\.|\,|\!|\?|\;)', text)
    index = 0
    list_format = []
    for token in tokens:
        list_format.append({
            "text": token,
            "index": index,
            "labels": []
        })
        index += len(token)
    list_format = [item for item in list_format if item['text'] != '']
    return list_format


def list_format_to_string(list_format):
    string = ""
    for item in list_format:
        string += item['text']
    return string


default_colour_map = {
    "SNOMED_CT": Fore.GREEN,
    "REGEX_QUESTION": Fore.RED,
    "REGEX_INFO": Fore.RED,
    "REGEX_COMPLAINT": Fore.MAGENTA,
    "QUESTION_RESPONSE": Fore.MAGENTA,
    "REGEX_CC_CATEGORY": Fore.CYAN,
    "REGEX_PMH_CATEGORY": Fore.CYAN,
    "REGEX_PSH_CATEGORY": Fore.CYAN,
    "REGEX_ALLERGIES_CATEGORY": Fore.CYAN,
    "REGEX_MEDICATIONS_CATEGORY": Fore.CYAN,
    "REGEX_FH_CATEGORY": Fore.CYAN,
    "REGEX_SH_CATEGORY": Fore.CYAN,
    "REGEX_MEDICATIONS": Fore.MAGENTA,
    "REGEX_NEGATION": Fore.MAGENTA,
    "REGEX_TIME": Fore.MAGENTA,
}

def list_format_to_coloured_string(list_format, colour_map=default_colour_map):
    string = ""
    for item in list_format:
        if len(item['labels']) > 0:
            last_label = item['labels'][-1]
            colour = colour_map.get(last_label['type'], Fore.CYAN)
            string += colour
        else:
            string += Style.RESET_ALL
        string += item['text']
    string += Style.RESET_ALL
    return string


def add_label_to_items(list_format, label, start_index, end_index):
    if start_index < 0:
        raise ValueError("Start index < 0 in add_label_to_items!")
    for item in list_format:
        if start_index <= item['index'] < end_index:
            item['labels'].append(label)
    return list_format


def find_response_to_question(next_turn, start_index=0):
    pattern = re.compile(r"(?:^|\. |\? |\! )([^\.\?\!]+?\.)")
    match = pattern.search(next_turn['text'], pos=start_index)
    return match


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--terms_folder", type=str, required=True)
    parser.add_argument("--transcript", type=str, required=True)
    args = parser.parse_args()

    terms = {}
    terms_categories = ['disorders', 'events', 'findings', 'procedures', 'products']
    for term_category in  terms_categories:
        with open(os.path.join(args.terms_folder, term_category + '_terms.txt'), 'r') as f:
            terms_in_category = [term.strip() for term in f.readlines()]
        terms[term_category] = terms_in_category

    with open(args.transcript, 'r') as f:
        transcript = json.load(f)

    new_transcript = {'transcript': []}
    for turn in transcript['transcript']:
        turn['list_format'] = string_to_list_format(turn['text'])
        new_transcript['transcript'].append(turn)
    transcript = new_transcript

    markers = {
        "QUESTION": [r"(?:^|\. |\? |\! )([^\.\?\!]+?\?)"],
        "INFO": [r"(where)", r"(when)", r"(why)", r"(who)", r"(how long)", r"(have you)", r"(is there)"],
        "COMPLAINT": [
            r"(I've been having[^\.\?\!]+(\.|\?|\!))",
            r"(I've had[^\.\?\!]+(\.|\?|\!))",
            r"(I have[^\.\?\!]+(\.|\?|\!))",
            r"(I had[^\.\?\!]+(\.|\?|\!))",
            r"(I got[^\.\?\!]+(\.|\?|\!))"
        ],
        "TIME": [
            r"((every|since|)? ?((couple)|(a few)|(several)|(one)|(two)|(three)|(four)|(five)|(six)|(seven)|(eight)|(nine)|(ten)|\d+)? ?(minutes?|hours?|days?|weeks?|months?|years?) ?(ago|after|before)?)",
        ],
        "CC_CATEGORY": [
            r"(what brings you in today)",
            r"(what('s| has) been going on)",
            r"(what('s| is) going on)",
        ],
        "PMH_CATEGORY": [
            r"(past medical history)",
        ],
        "PSH_CATEGORY": [
            r"(surgeries)"
        ],
        "ALLERGIES_CATEGORY": [
            r"(allergies)"
        ],
        "MEDICATIONS_CATEGORY": [
            r"(medications)",
        ],
        "FH_CATEGORY": [
            r"(family)(?: |\.|\?|\!)",
            r"(family history)(?: |\.|\?|\!)",
            r"(mom and dad)(?: |\.|\?|\!)",
            r"(father)(?: |\.|\?|\!)",
            r"(mother)(?: |\.|\?|\!)",
            r"(mom)(?: |\.|\?|\!)",
            r"(dad)(?: |\.|\?|\!)"
        ],
        "SH_CATEGORY": [
            r"(drug use)",
            r"(tobacco)",
            r"(smoke)",
            r"(smoking)",
            r"(alcohol)",
        ],
        "MEDICATIONS": [
            r"(I take[^\.\?\!]+(\.|\?|\!))",
            r"(I took[^\.\?\!]+(\.|\?|\!))",
        ],
        "NEGATION": [
            r"(?: |^)(no)(?: |\.|\?)"
        ],
    }

    # REGEX
    for turn_idx, turn in enumerate(transcript['transcript']):
        for marker_category, marker_regexes_list in markers.items():
            for marker_regex in marker_regexes_list:
                matches = list(re.finditer(marker_regex, turn['text'], re.IGNORECASE))
                if len(matches) > 0:
                    for match in matches:
                        match_text = match.groups()[0]
                        # Need to manually find index since match.span returns span of full match (including non-capturing groups)
                        start_index = turn['text'].lower().find(match_text.lower(), match.span()[0]) 
                        end_index = start_index + len(match_text)
                        label = {
                            "type": "REGEX_" + marker_category,
                            "match": match_text,
                            "category": marker_category
                        }
                        add_label_to_items(turn['list_format'], label, start_index, end_index)
                        # If we found a question, find the response (next non-question statement)
                        if marker_category == "QUESTION":
                            pass

    # SNOMED CT
    for turn in transcript['transcript']:
        for term_category, terms_list in terms.items():
            for term in terms_list:
                if match_full_term(term, turn['text']):
                    label = {
                        "type": "SNOMED_CT",
                        "term": term,
                        "category": term_category
                    }
                    start_index = turn['text'].lower().find(term.lower())
                    end_index = start_index + len(term)
                    add_label_to_items(turn['list_format'], label, start_index, end_index)


    for turn in transcript['transcript']:
        coloured_text = list_format_to_coloured_string(turn['list_format'])
        print("{}: {}".format(turn['speaker'], coloured_text))
        print()
