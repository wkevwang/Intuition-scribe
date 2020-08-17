# To run: python -m pytest scribe_test.py

import pytest

from scribe import *
from colorama import Fore


def test_string_to_list_format():
    string = "Hello world, hi? There."
    list_format = string_to_list_format(string)
    assert list_format[0]['text'] == "Hello"
    assert list_format[0]['index'] == 0
    assert list_format[1]['text'] == " "
    assert list_format[1]['index'] == 5
    assert list_format[2]['text'] == "world"
    assert list_format[2]['index'] == 6
    assert list_format[3]['text'] == ","
    assert list_format[3]['index'] == 11
    assert list_format[4]['text'] == " "
    assert list_format[4]['index'] == 12
    assert list_format[5]['text'] == "hi"
    assert list_format[5]['index'] == 13
    assert list_format[6]['text'] == "?"
    assert list_format[6]['index'] == 15
    assert list_format[7]['text'] == " "
    assert list_format[7]['index'] == 16
    assert list_format[8]['text'] == "There"
    assert list_format[8]['index'] == 17
    assert list_format[9]['text'] == "."
    assert list_format[9]['index'] == 22


def test_list_format_to_string():
    original_string = "Hello world, hi? There."
    list_format = string_to_list_format(original_string)
    string = list_format_to_string(list_format)
    assert string == original_string


def test_print_list_format_1():
    colour_map = {
        "SNOMED_CT": Fore.GREEN,
        "REGEX": Fore.RED
    }
    list_format = [{
        "text": "Hello",
        "index": 0,
        "labels": [
            { "type": "SNOMED_CT" }
        ]
    }, {
        "text": " ",
        "index": 5,
        "labels": [
            { "type": "SNOMED_CT" }
        ]
    }, {
        "text": "world",
        "index": 6,
        "labels": [
            { "type": "SNOMED_CT" }
        ]
    }]
    coloured_string = list_format_to_coloured_string(list_format, colour_map)
    assert coloured_string == '\x1b[32mHello\x1b[32m \x1b[32mworld\x1b[0m'


def test_print_list_format_2():
    colour_map = {
        "SNOMED_CT": Fore.GREEN,
        "REGEX": Fore.RED
    }
    list_format = [{
        "text": "Hello",
        "index": 0,
        "labels": [
            { "type": "SNOMED_CT" }
        ]
    }, {
        "text": " ",
        "index": 5,
        "labels": []
    }, {
        "text": "world",
        "index": 6,
        "labels": []
    }]
    coloured_string = list_format_to_coloured_string(list_format, colour_map)
    assert coloured_string == '\x1b[32mHello\x1b[0m \x1b[0mworld\x1b[0m'


def test_print_list_format_2():
    colour_map = {
        "SNOMED_CT": Fore.GREEN,
        "REGEX": Fore.RED
    }
    list_format = [{
        "text": "Hello",
        "index": 0,
        "labels": [
            { "type": "REGEX" }
        ]
    }, {
        "text": " ",
        "index": 5,
        "labels": [
            { "type": "REGEX" }
        ]
    }, {
        "text": "world",
        "index": 6,
        "labels": [
            { "type": "REGEX" },
            { "type": "SNOMED_CT" }
        ]
    }, {
        "text": " ",
        "index": 11,
        "labels": [
            { "type": "REGEX" }
        ]
    }, {
        "text": "there",
        "index": 12,
        "labels": [
            { "type": "REGEX" }
        ]
    }]
    coloured_string = list_format_to_coloured_string(list_format, colour_map)
    assert coloured_string == '\x1b[31mHello\x1b[31m \x1b[32mworld\x1b[31m \x1b[31mthere\x1b[0m'


def test_add_label_to_items_1():
    string = "Hello world, hi? There."
    list_format = string_to_list_format(string)
    add_label_to_items(list_format, { "type": "REGEX" }, 6, 6 + len("world, hi"))
    assert len(list_format[0]['labels']) == 0
    assert len(list_format[1]['labels']) == 0
    assert len(list_format[2]['labels']) == 1
    assert len(list_format[3]['labels']) == 1
    assert len(list_format[4]['labels']) == 1
    assert len(list_format[5]['labels']) == 1
    assert len(list_format[6]['labels']) == 0
    assert len(list_format[7]['labels']) == 0
    assert len(list_format[8]['labels']) == 0
    assert len(list_format[9]['labels']) == 0

def test_add_label_to_items_1():
    string = "Hello world, hi? There."
    list_format = string_to_list_format(string)
    add_label_to_items(list_format, { "type": "REGEX" }, 6, 6 + len("world, hi"))
    add_label_to_items(list_format, { "type": "REGEX" }, 13, 13 + len("hi? There"))
    assert len(list_format[0]['labels']) == 0
    assert len(list_format[1]['labels']) == 0
    assert len(list_format[2]['labels']) == 1
    assert len(list_format[3]['labels']) == 1
    assert len(list_format[4]['labels']) == 1
    assert len(list_format[5]['labels']) == 2
    assert len(list_format[6]['labels']) == 1
    assert len(list_format[7]['labels']) == 1
    assert len(list_format[8]['labels']) == 1
    assert len(list_format[9]['labels']) == 0


def test_find_first_sentence_response_to_question():
    next_turn = {
        "text": "Yes, it's me. That's me."
    }
    response_match = find_first_sentence_response_to_question(next_turn)
    assert response_match.group() == "Yes, it's me."


def test_slice_list_format():
    string = "Hello world, hi? There."
    list_format = string_to_list_format(string)
    sliced_list_format = slice_list_format(list_format, 13, 16)
    assert sliced_list_format[0]['text'] == 'hi'
    assert sliced_list_format[1]['text'] == '?'
