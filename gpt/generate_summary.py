"""

"""

import json
import os
import numpy as np
import argparse
import sys
from nltk.stem import WordNetLemmatizer
from nltk.stem.snowball import SnowballStemmer
from nltk.stem.porter import *
import tensorflow as tf

sys.path.append(os.path.dirname(os.path.abspath(__file__))) # Import current folder to sys.path
import model, sample, encoder

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # Import parent folder to sys.path
from snomed_ct import snomed
from utilities import *
from constants import REGEX_MARKERS


# ------------- Checking summary -------------
def clean_word(word):
    word = word.lower()
    # word = lemmatizer.lemmatize(word)
    word = stemmer.stem(word)
    return word

lemmatizer = WordNetLemmatizer()
stemmer = SnowballStemmer("english")
allowed_words = [
    "to", "the", "a", "it", "and", "patient", "says", "had", "in", "his",
    "her", "he", "she", '.', 'as', ',', 'start', 'at', 'while', 'was', "began",
    "noticing", "does", "not", "saw", "that", "patient's", "doesn't", "is",
    "felt", "feels",
]
allowed_words = [clean_word(word) for word in allowed_words]
not_allowed_words = [
    "I", "my", "?", "!", "your", '..', "I'll",
]
not_allowed_words = [clean_word(word) for word in not_allowed_words]

def check_summary(terms, question, answer, summary,
                  require_snomed_terms=False):
    """
    Check that summary only contains words from the question and answer, or stop words,
    and also contains all of the SNOMED terms present in the question and answer.
    """
    question_words = [clean_word(word) for word in split_on_spaces_and_punctuation(question)]
    answer_words = [clean_word(word) for word in split_on_spaces_and_punctuation(answer)]
    all_allowed_words = set(question_words + answer_words + allowed_words)

    snomed_terms = []
    for term_category, terms_list in terms.items():
        for term in terms_list:
            if match_full_term(term, question):
                snomed_terms.append(term)
            elif match_full_term(term, answer):
                snomed_terms.append(term)

    summary_words = [clean_word(word) for word in split_on_spaces_and_punctuation(summary)]
    for summary_word in summary_words:
        if summary_word.lower() not in all_allowed_words:
            return False, "{} not in allowed words".format(summary_word)
        if summary_word.lower() in not_allowed_words:
            return False, "{} not allowed".format(summary_word)
    if require_snomed_terms:
        for snomed_term in snomed_terms:
            if not match_full_term(snomed_term, summary):
                return False, "SNOMED term '{}' missing".format(snomed_term)
    
    return True, "Passed"

# ------------- Determine context category -------------

with open('context.json', 'r') as f:
    context_dict = json.load(f)

def determine_context_category(question, answer):
    """
    Depending on the text in question and answer, determine which category of
    context text to use for few-shot tuning.
    """
    question = question.strip().lower()
    answer = answer.strip().lower()
    all_text = question + ' ' + answer
    for marker_regex in REGEX_MARKERS['NEGATION']:
        if re.search(marker_regex, answer, re.IGNORECASE):
            return "Negation"
    for marker_regex in REGEX_MARKERS['SH_CATEGORY']:
        if re.search(marker_regex, all_text, re.IGNORECASE):
            return "Social History"
    for marker_regex in REGEX_MARKERS['FH_CATEGORY']:
        if re.search(marker_regex, all_text, re.IGNORECASE):
            return "Family History"
    for marker_regex in REGEX_MARKERS['MEDICATIONS_CATEGORY']:
        if re.search(marker_regex, all_text, re.IGNORECASE):
            return "Medication" 
    if match_full_term('pain', all_text):
        return "Pain" 
    return "General"

# ------------- Summarize -------------

def summarize(question, answer, batch_size=10, max_batches=3):
    summaries_batch = []
    context_category = determine_context_category(question, answer)
    context_text = context_dict[context_category]
    context_tokens = enc.encode("{}Question: {}\nAnswer: {}\nSummary: ".format(context_text, question, answer))
    for batch_idx in range(max_batches):
        print("Batch {} of {}...".format(batch_idx + 1, max_batches))
        out = sess.run(output, feed_dict={
            context: [context_tokens for _ in range(batch_size)]
        })[:, len(context_tokens):]
        for i in range(batch_size):
            text = enc.decode(out[i])
            text = text.replace(u'\xa0', '') # Remove non-breaking space which, for some reason, is at the beginning of text
            summary = text.split('\n')[0]
            summary_valid, reason = check_summary(snomed_terms, question, answer, summary)
            summaries_batch.append({
                "context_category": context_category,
                "summary": summary,
                "summary_valid": summary_valid,
                "reason": reason,
            })
    return summaries_batch

sess = None
context = None
enc = None
output = None
snomed_terms = None

def init_model(model_name="774M", length=30, batch_size=10, terms_folder="terms", temperature=1.0,
               top_k=40, top_p=1.0, seed=None):
    global sess, context, enc, output, snomed_terms
    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
    snomed_terms = snomed.load_snomed_terms(terms_folder)

    enc = encoder.get_encoder(model_name, models_dir)
    hparams = model.default_hparams()
    with open(os.path.join(models_dir, model_name, 'hparams.json')) as f:
        hparams.override_from_dict(json.load(f))

    tf.compat.v1.disable_eager_execution()
    sess = tf.Session()
    context = tf.placeholder(tf.int32, [batch_size, None])
    np.random.seed(seed)
    tf.set_random_seed(seed)
    output = sample.sample_sequence(
        hparams=hparams, length=length,
        context=context,
        batch_size=batch_size,
        temperature=temperature, top_k=top_k, top_p=top_p
    )

    saver = tf.train.Saver()
    ckpt = tf.train.latest_checkpoint(os.path.join(models_dir, model_name))
    saver.restore(sess, ckpt)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", default="774M", type=str, required=False)
    parser.add_argument("--length", default=30, type=int, required=False)
    parser.add_argument("--batch_size", default=10, type=int, required=False)
    parser.add_argument("--terms_folder", default='terms', type=str, required=False)
    parser.add_argument("--temperature", default=1.0, type=float, required=False)
    parser.add_argument("--top_k", default=40, type=int, required=False)
    parser.add_argument("--top_p", default=1.0, type=float, required=False)
    parser.add_argument("--seed", default=None, type=int, required=False)
    parser.add_argument("--max_batches_per_qa", default=5, type=int, required=False)
    args = parser.parse_args()

    init_model(model_name=args.model_name, length=args.length, batch_size=args.batch_size,
               terms_folder=args.terms_folder, temperature=args.temperature,
               top_k=args.top_k, top_p=args.top_p, seed=args.seed)

    while True:
        question = input("Question: ")
        answer = input("Answer: ")
        valid_summary_found = False
        attempts = 0

        while not valid_summary_found and attempts < args.max_batches_per_qa:
            summaries_batch = summarize(question, answer,
                                        batch_size=args.batch_size, max_batches=args.max_batches_per_qa)
            for summary in summaries_batch:
                context_category = summary['context_category']
                summary_text = summary['summary']
                summary_valid = summary['summary_valid']
                reason = summary['reason']
                print("Summary: {} | Context used: {} | Passed check: {} ({})".format(summary_text, context_category, summary_valid, reason))
                print("---------------------------")
                if summary_valid:
                    break
            attempts += args.max_batches_per_qa * args.batch_size
