# To run: python -m pytest generate_summary_test.py

import pytest

from generate_summary import *

snomed_terms = snomed.load_snomed_terms('terms')

def test_check_summary_1():
    question = "AA BB?"
    answer = "AA."
    summary = "AA."
    summary_valid, _ = check_summary(snomed_terms, question, answer, summary)
    assert summary_valid == True


def test_check_summary_2():
    question = "AA BB?"
    answer = "CC."
    summary = "AA."
    summary_valid, _ = check_summary(snomed_terms, question, answer, summary)
    assert summary_valid == True


def test_check_summary_3():
    question = "AA BB?"
    answer = "CC."
    summary = "his she AA."
    summary_valid, _ = check_summary(snomed_terms, question, answer, summary)
    assert summary_valid == True


def test_check_summary_4():
    question = "AA BB?"
    answer = "CC."
    summary = "his she AAA."
    summary_valid, _ = check_summary(snomed_terms, question, answer, summary)
    assert summary_valid == False


def test_check_summary_5():
    question = "AA BB hypertension?"
    answer = "CC."
    summary = "his she AAA."
    summary_valid, _ = check_summary(snomed_terms, question, answer, summary)
    assert summary_valid == False


def test_check_summary_6():
    question = "AA BB AAA hypertension?"
    answer = "CC."
    summary = "his she AAA hypertension."
    summary_valid, _ = check_summary(snomed_terms, question, answer, summary)
    assert summary_valid == True
