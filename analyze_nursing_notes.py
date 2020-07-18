"""
Analyzes .txt nursing note file, generating a summary for each note into categories.
"""

import argparse
import pandas as pd
import os
from keywords import keywords
import regex as re
from utilities import *

categories = [
    "Clinical Status",
    "Mobility",
    "Nutrition",
    "Toileting",
    "Behaviour",
]


def match_full_term(term, phrase):
    term = term.lower()
    phrase = phrase.lower()
    if term in phrase:
        idx = phrase.index(term)
        if (idx == 0 or (phrase[idx - 1] == ' ')) and ((idx + len(term) == len(phrase)) or phrase[idx + len(term)] == ' '):
            return True
    return False


def match_regex_full_term(pattern, phrase):
    return re.search("(^| |:|-){}($| |:|-)".format(pattern), phrase, re.IGNORECASE)

# if re.search('(^| ){}($| )'.format(re.escape(term)), phrase, re.IGNORECASE):
# idx = phrase.index(term); (idx == 0 or (phrase[idx - 1] == ' ')) and ((idx + len(term) == len(phrase)) or phrase[idx + len(term)] == ' ')

template_text_list = [
    "HANDOVER NOTE",
    "Recent changes:",
    "Anticipated changes:",
    "What to watch out for:",
    "Stability of the patient:",
    "Summary:",
]


def clean_phrases(phrases):
    phrases_lowercase = set()
    final_phrases = []
    for phrase in phrases:
        for template_text in template_text_list:
            phrase = re.sub(re.escape(template_text), '', phrase, re.IGNORECASE)
        phrase = phrase.strip('-')
        phrase = phrase.strip()
        if phrase.lower() in phrases_lowercase:
            continue
        phrases_lowercase.add(phrase.lower())
        final_phrases.append(capitalize(phrase))
    return final_phrases


def print_summary(summary):
    for category in categories:
        if len(summary[category]) > 0:        
            print("\t{}".format(category))
            for phrase in clean_phrases(summary[category]):
                print("\t\t- {}".format(phrase))

temp_delimiter = '|||'
def build_summary(note_for_day):
        # Replace all delimiters with temp character for splitting
    delimiters = ['\n', '.', '(', ')', ';', ',']
    for d in delimiters:
        note_for_day = note_for_day.replace(d, temp_delimiter)
    phrases = note_for_day.split(temp_delimiter)
    summary = {category: [] for category in categories}
    for phrase in phrases:
        phrase_matched = False
        for keyword_category, keywords_list in keywords.items():
            for keyword_regex in keywords_list:
                if match_regex_full_term(keyword_regex, phrase):
                    summary[keyword_category].append(phrase)
                    # print("Phrase: {} | Term: {} | Category: {}".format(phrase, keyword_regex, keyword_category))
                    phrase_matched = True
                    break
            if phrase_matched:
                break
        if phrase_matched:
            continue
        for term in terms:
            if len(term) > len(phrase):
                continue
            if match_full_term(term, phrase):
                summary["Clinical Status"].append(phrase)
                # print("Phrase: {} | Term: {} | Category: Clinical Status (SNOMED CT)".format(phrase, term))
                break
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--terms_file", type=str, required=True)
    parser.add_argument("--notes_file", type=str, required=True)
    args = parser.parse_args()

    terms = []
    with open(args.terms_file, 'r') as f:
        for line in f:
            terms.append(line.rstrip())

    note_lines = []
    # Need 'utf-8-sig' to account for BOM character at the beginning (that docx->txt creates)
    with open(args.notes_file, 'r', encoding='utf-8-sig') as f:
        for line in f:
            note_lines.append(line.strip())
    
    current_date = None
    note_for_day = ""

    for line in note_lines:
        date = to_date(line)
        if date:
            if current_date != None:
                if date.month == current_date.month and date.day == current_date.day: # If it's the same day
                    current_date = date
                    continue
                else: # If it's a different day, print summary
                    summary_for_day = build_summary(note_for_day)
                    print_summary(summary_for_day)
                    note_for_day = ""
                    print("\n{}".format(date.strftime("%B %d"))) # Print date
                    current_date = date
            else:
                print("\n{}".format(date.strftime("%B %d"))) # Print date
                current_date = date
        else:
            note_for_day += "{}{}".format(temp_delimiter, line)
    summary_for_day = build_summary(note_for_day)
    print_summary(summary_for_day)
