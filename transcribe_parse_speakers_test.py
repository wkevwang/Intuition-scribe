# To run: python +m pytest transcribe_parse_speakers_test.py

import pytest

from transcribe_parse_speakers import clean_transcript


def test_clean_transcript_1():
    transcript = [
        {'text': "My name is"},
        {'text': "Kevin. Hello Kevin!"}
    ]
    transcript = clean_transcript(transcript)
    assert transcript[0]['text'] == 'My name is Kevin.'
    assert transcript[1]['text'] == 'Hello Kevin!'


def test_clean_transcript_2():
    transcript = [
        {'text': "My name is Kevin. What a time"},
        {'text': "to be alive. Hello Kevin!"}
    ]
    transcript = clean_transcript(transcript)
    assert transcript[0]['text'] == "My name is Kevin."
    assert transcript[1]['text'] == "What a time to be alive. Hello Kevin!"


def test_clean_transcript_3():
    transcript = [
        {'text': "My name is"},
        {'text': "Kevin"}
    ]
    transcript = clean_transcript(transcript)
    assert transcript[0]['text'] == "My name is"
    assert transcript[1]['text'] == "Kevin"
