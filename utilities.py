from datetime import datetime
import regex as re
import pprint
from colorama import Fore, Style
from constants import *


def capitalize(text):
    return text[0].upper() + text[1:]


def to_date(string):
    """
    Use strptime to try to parse the date. If it's not a date in that specified
    format, strptime will throw an exception.

    Documentation on format: https://www.journaldev.com/23365/python-string-to-datetime-strptime
    """
    string = string.replace(',', '').replace(':', '')
    date = None
    try:
        date = datetime.strptime(string, "%B %d %H%M")
    except ValueError:
        # Not a date
        pass
    try:
        date = datetime.strptime(string, "%b %d %H%M")
    except ValueError:
        # Not a date
        pass
    return date


def match_full_term(term, phrase):
    """
    Returns True if the full term is found in the phrase
    e.g. 
    term="red" and phrase="redness" => False
    term="red" and phrase="a red rash" => True
    """
    term = term.lower()
    phrase = phrase.lower()
    if term in phrase:
        idx = phrase.index(term)
        if ((idx == 0 or (phrase[idx - 1] == ' ')) and 
            ((idx + len(term) == len(phrase)) or phrase[idx + len(term)] in [' ', '.', ',', ';', '?', '!'])):
            return True
    return False


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


def split_on_spaces_and_punctuation(text):
    """
    Split text on spaces and punctuation, keeping the spaces and punctuation.
    """
    tokens = re.split(r'( |\.|\,|\!|\?|\;)', text)
    tokens = [token for token in tokens if token != '']
    return tokens


pp = pprint.PrettyPrinter(indent=4)
def prprint(data):
    pp.pprint(data)


def string_to_list_format(text):
    """
    Convert text (string) to a list of dicts, with each dict containing the keys:
        - text: str
        - index: int
        - labels: list of dict
    Each dict's text is a full word, whitespace, or punctuation
    """
    tokens = split_on_spaces_and_punctuation(text)
    index = 0
    list_format = []
    for token in tokens:
        list_format.append({
            "text": token,
            "index": index,
            "labels": []
        })
        index += len(token)
    list_format = [item for item in list_format]
    return list_format


def list_format_to_string(list_format):
    string = ""
    for item in list_format:
        string += item['text']
    return string


def slice_list_format(list_format, start_index, end_index):
    sliced_list_format = []
    for token in list_format:
        if start_index <= token['index'] < end_index:
            sliced_list_format.append(token)
    return sliced_list_format


def list_format_to_coloured_string(list_format, colour_map=COLOUR_MAP):
    string = ""
    for item in list_format:
        if len(item['labels']) > 0:
            last_label = item['labels'][-1]
            type_str = last_label['type']
            if type_str == 'REGEX':
                type_str += '_' + last_label['category']
            colour = colour_map.get(type_str, Fore.CYAN)
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


def find_list_format_slice_with_label_id(transcript, label_id):
    sliced_list_format = []
    for turn in transcript:
        for token in turn['list_format']:
            for label in token['labels']:
                if label['label_id'] == label_id:
                    sliced_list_format.append(token)
    return sliced_list_format


def list_format_contains_type(list_format, label_type, category=None):
    for token in list_format:
        for label in token['labels']:
            if label['type'] == label_type:
                if (category is None) or (label['category'] == category):
                    return True            
    return False

