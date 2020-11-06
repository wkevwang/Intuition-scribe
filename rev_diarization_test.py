# To run: python -m pytest rev_diarization_test.py

import pytest

from rev_diarization import assign_full_sentences_to_speaker


def test_assign_full_sentences_to_speaker():
    transcript_elements = [
        {"speaker": "Patient", "value": "Um"}, # 0
        {"speaker": "Patient", "value": ","},
        {"speaker": "Patient", "value": "I've"},
        {"speaker": "Patient", "value": "been"},
        {"speaker": "Doctor", "value": "having"},
        {"speaker": "Doctor", "value": "pretty"},
        {"speaker": "Doctor", "value": "bad"},
        {"speaker": "Patient", "value": "neck"},
        {"speaker": "Patient", "value": "pain"},
        {"speaker": "Patient", "value": "."}, # 9
        {"speaker": "Doctor", "value": "Oh"}, # 10
        {"speaker": "Doctor", "value": ","},
        {"speaker": "Doctor", "value": "no"},
        {"speaker": "Doctor", "value": "."}, # 13
    ]
    assign_full_sentences_to_speaker(transcript_elements)
    for i in range(0, 10):
        assert transcript_elements[i]["speaker"] == "Patient"
    for i in range(10, 14):
        assert transcript_elements[i]["speaker"] == "Doctor"


def test_assign_full_sentences_to_speaker_even_split():
    transcript_elements = [
        {"speaker": "Patient", "value": "A"}, # 0
        {"speaker": "Patient", "value": "A"},
        {"speaker": "Doctor", "value": "B"},
        {"speaker": "Doctor", "value": "B"},
        {"speaker": "Patient", "value": "."}, # 4
        {"speaker": "Patient", "value": "A"}, # 5
        {"speaker": "Patient", "value": "."}, # 6
    ]
    assign_full_sentences_to_speaker(transcript_elements)
    for i in range(0, 4):
        assert transcript_elements[i]["speaker"] == "Patient"
    for i in range(4, 7):
        assert transcript_elements[i]["speaker"] == "Patient"