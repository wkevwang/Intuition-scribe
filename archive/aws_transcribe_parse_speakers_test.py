# To run: python -m pytest transcribe_parse_speakers_test.py

import pytest

from transcribe_parse_speakers import *


def test_move_unfinished_sentences_1():
    transcript = [
        {'text': "My name is"},
        {'text': "Kevin. Hello Kevin!"}
    ]
    transcript = move_unfinished_sentences(transcript)
    assert transcript[0]['text'] == 'My name is Kevin.'
    assert transcript[1]['text'] == 'Hello Kevin!'


def test_move_unfinished_sentences_2():
    transcript = [
        {'text': "My name is Kevin. What a time"},
        {'text': "to be alive. Hello Kevin!"}
    ]
    transcript = move_unfinished_sentences(transcript)
    assert transcript[0]['text'] == "My name is Kevin."
    assert transcript[1]['text'] == "What a time to be alive. Hello Kevin!"


def test_move_unfinished_sentences_3():
    transcript = [
        {'text': "My name is"},
        {'text': "Kevin"}
    ]
    transcript = move_unfinished_sentences(transcript)
    assert transcript[0]['text'] == "My name is"
    assert transcript[1]['text'] == "Kevin"


def test_split_last_question_1():
    text = "A? B."
    a, b = split_last_question(text)
    assert a == "A?"
    assert b == "B."


def test_split_last_question_2():
    text = "A? B. C?"
    a, b = split_last_question(text)
    assert a == "A?"
    assert b == "B. C?"


def test_split_last_question_3():
    text = "A? B. C."
    a, b = split_last_question(text)
    assert a == "A?"
    assert b == "B. C."


def test_split_last_question_4():
    text = "A? B. C? D."
    a, b = split_last_question(text)
    assert a == "A?"
    assert b == "B. C? D."


def test_split_last_question_5():
    text = "A? B? C. D."
    a, b = split_last_question(text)
    assert a == "A? B?"
    assert b == "C. D."


def test_split_last_question_6():
    text = "A? B? C. D?"
    a, b = split_last_question(text)
    assert a == "A? B?"
    assert b == "C. D?"


def test_split_last_question_7():
    text = "A?"
    a, b = split_last_question(text)
    assert a == "A?"
    assert b == ""


def test_split_last_question_8():
    text = "A."
    a, b = split_last_question(text)
    assert a == "A."
    assert b == ""


def test_split_last_question_9():
    text = "A. B? C."
    a, b = split_last_question(text)
    assert a == "A. B?"
    assert b == "C."


def test_split_last_statement_1():
    text = "B. C? D."
    a, b = split_last_statement(text)
    assert a == "B."
    assert b == "C? D."


def test_move_question_responses_1():
    transcript = [
        { 'speaker': 'Doctor', 'text': "A? B." }
    ]
    new_transcript = move_question_responses(transcript)
    assert new_transcript[0]['speaker'] == 'Doctor'
    assert new_transcript[0]['text'] == 'A?'
    assert new_transcript[1]['speaker'] == 'Patient'
    assert new_transcript[1]['text'] == 'B.'


def test_move_question_responses_2():
    transcript = [
        { 'speaker': 'Doctor', 'text': "A? B. C?" }
    ]
    new_transcript = move_question_responses(transcript)
    assert new_transcript[0]['speaker'] == 'Doctor'
    assert new_transcript[0]['text'] == 'A?'
    assert new_transcript[1]['speaker'] == 'Patient'
    assert new_transcript[1]['text'] == 'B.'
    assert new_transcript[2]['speaker'] == 'Doctor'
    assert new_transcript[2]['text'] == 'C?'


def test_move_question_responses_3():
    transcript = [
        { 'speaker': 'Doctor', 'text': "A? B. C." }
    ]
    new_transcript = move_question_responses(transcript)
    assert new_transcript[0]['speaker'] == 'Doctor'
    assert new_transcript[0]['text'] == 'A?'
    assert new_transcript[1]['speaker'] == 'Patient'
    assert new_transcript[1]['text'] == 'B. C.'


def test_move_question_responses_4():
    transcript = [
        { 'speaker': 'Doctor', 'text': "A? B. C? D." }
    ]
    new_transcript = move_question_responses(transcript)
    assert new_transcript[0]['speaker'] == 'Doctor'
    assert new_transcript[0]['text'] == 'A?'
    assert new_transcript[1]['speaker'] == 'Patient'
    assert new_transcript[1]['text'] == 'B.'
    assert new_transcript[2]['speaker'] == 'Doctor'
    assert new_transcript[2]['text'] == 'C?'
    assert new_transcript[3]['speaker'] == 'Patient'
    assert new_transcript[3]['text'] == 'D.'


def test_move_question_responses_5():
    transcript = [
        { 'speaker': 'Doctor', 'text': "A? B." },
        { 'speaker': 'Patient', 'text': "C." },
    ]
    new_transcript = move_question_responses(transcript)
    assert new_transcript[0]['speaker'] == 'Doctor'
    assert new_transcript[0]['text'] == 'A?'
    assert new_transcript[1]['speaker'] == 'Patient'
    assert new_transcript[1]['text'] == 'B. C.'


def test_move_question_responses_6():
    transcript = [
        { 'speaker': 'Patient', 'text': "Z." },
        { 'speaker': 'Doctor', 'text': "A? B." },
        { 'speaker': 'Patient', 'text': "C." },
    ]
    new_transcript = move_question_responses(transcript)
    assert new_transcript[0]['speaker'] == 'Patient'
    assert new_transcript[0]['text'] == 'Z.'
    assert new_transcript[1]['speaker'] == 'Doctor'
    assert new_transcript[1]['text'] == 'A?'
    assert new_transcript[2]['speaker'] == 'Patient'
    assert new_transcript[2]['text'] == 'B. C.'
