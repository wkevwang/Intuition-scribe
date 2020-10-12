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


context_text = """Question: So how long's the pain been going on?
Answer: Probably about two days.
Summary: The pain has been going on for about two days.
Question: Anything happened a couple days ago out of the ordinary?
Answer: I was in a small car accident.
Summary: Patient was in a small car accident.
Question: So when exactly did the pain start about how many hours after the accident?
Answer: I would probably say maybe 4 to 6 hours after.
Summary: The pain started 4 to 6 hours after the accident.
Question: And where is the pain bothering you specifically?
Answer: The pain is bothering the patient on the back of the neck and on the sides of the neck.
Question: And can you describe the pain to me?
Answer: It just feels like a tight kind of dull pain.
Summary: The pain feels like the a tight kind of dull pain.
Question: And would you say since the accident since that evening, has the pain been constant or is the pain getting worse?
Answer: It feels like it's getting worse.
Summary: The pain feels like it's getting worse.
Question: When did you first notice the pain?
Answer: This was maybe two days ago.
Summary: The patient noticed the pain two days ago.
Question: How would you describe this pain that you've been feeling?
Answer: It's just kind of ah, kind of aching.
Summary: Patient describes pain as aching.
Question: Do you drink any alcohol?
Answer: Just on the weekends.
Summary: Patient drinks alcohol on the weekends.
Question: Can you describe the pain for me?
Answer: It was like someone sitting on my chest.
Summary: Patient describes pain as like someone sitting on chest.
Question: Would you say the pain has gotten worse as well?
Answer: It's stayed about the same.
Summary: The pain has stayed about the same.
Question: Have you been coughing anything up?
Answer: Yes, like green sputum.
Summary: Patient coughing up green sputum.
Question: Can you tell me a bit more about the pain?
Answer: It was happening in my chest and the whole kind of episode lasted about 40 minutes, which is kind of the point of which the ambulance came and gave me some pain killers to help.
Summary: The pain was happening in patient's chest and lasted about 40 minutes until ambulance came and gave patient pain killers.
Question: Just anything that seems to make the pain worse?
Answer: Yeah, I feel that, like, if I press around the chest it can be. It can be a bit tender.
Summary: Pressing around the chest makes pain worse.
Question: Have you noticed any sweating?
Answer: I do feel a bit but warmer. I wouldn't say I'm sweating a lot more.
Summary: Patient feels a bit warmer but is not sweating a lot more.
Question: Can you explain exactly what you mean when you say breathlessness?
Answer: Yeah, it's just that, you know, struggling to kind of just catch my breath, especially when I'm walking down when I'm walking upstairs.
Summary: Patient struggles to catch breath, especially when walking upstairs.
"""



"""
Question: Would you say the pain came on gradually or suddenly came quite suddenly?
Answer: Actually, literally as I was just leaving the house, all of a sudden I felt this pain.
Summary: """


"""
Question: When did you first notice the blurred vision?
Answer: I first noticed it last week, when my eye started hurting.
Summary: """


"""
Question: What happens when you move your arm in a circle?
Answer: Well, my arm makes a cracking sound when I do that.
"""


"""
Question: Do you experience pain when you apply pressure on your left or right leg?
Answer: I don't experience pain on either leg.
"""

lemmatizer = WordNetLemmatizer()
stemmer = SnowballStemmer("english")

def clean_word(word):
    word = word.lower()
    # word = lemmatizer.lemmatize(word)
    word = stemmer.stem(word)
    return word


allowed_words = [
    "to", "the", "a", "it", "and", "patient", "says", "had", "in", "his",
    "her", "he", "she", '.', 'as', ',', 'start', 'at', 'while', 'was', "began",
    "noticing", "does", "not", "saw", "that", "patient's", "doesn't"
]
allowed_words = [clean_word(word) for word in allowed_words]
not_allowed_words = [
    "I", "my", "?", "!", "your", '..', "I'll",
]
not_allowed_words = [clean_word(word) for word in not_allowed_words]

def check_summary(terms, question, answer, summary):
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
    for snomed_term in snomed_terms:
        if not match_full_term(snomed_term, summary):
            return False, "SNOMED term '{}' missing".format(snomed_term)
    
    return True, "Passed"


def summarize(question, answer, max_batches=3):
    summaries_batch = []
    context_tokens = enc.encode("{}Question: {}\nAnswer: {}\nSummary: ".format(context_text, question, answer))
    for batch_idx in range(max_batches):
        print("Batch {} of {}...".format(batch_idx + 1, max_batches))
        out = sess.run(output, feed_dict={
            context: [context_tokens for _ in range(args.batch_size)]
        })[:, len(context_tokens):]
        for i in range(args.batch_size):
            text = enc.decode(out[i])
            text = text.replace(u'\xa0', '') # Remove non-breaking space which, for some reason, is at the beginning of text
            summary = text.split('\n')[0]
            summary_valid, reason = check_summary(snomed_terms, question, answer, summary)
            summaries_batch.append({
                "summary": summary,
                "summary_valid": summary_valid,
                "reason": reason,
            })
            if summary_valid:
                return summaries_batch
    return summaries_batch


parser = argparse.ArgumentParser()
parser.add_argument("--model_name", default="774M", type=str, required=False)
parser.add_argument("--length", default=30, type=int, required=False)
parser.add_argument("--batch_size", default=10, type=int, required=False)
parser.add_argument("--terms_folder", default='terms', type=str, required=False)
parser.add_argument("--print_all", default=False, action='store_true', required=False)
parser.add_argument("--temperature", default=1.0, type=float, required=False)
parser.add_argument("--top_k", default=40, type=int, required=False)
parser.add_argument("--top_p", default=1.0, type=float, required=False)
parser.add_argument("--seed", default=None, type=int, required=False)
parser.add_argument("--max_batches_per_qa", default=5, type=int, required=False)
if __name__ == "__main__":
    args = parser.parse_args()
else:
    args = parser.parse_args([])

models_dir = 'models'
models_dir = os.path.expanduser(os.path.expandvars(models_dir))
snomed_terms = snomed.load_snomed_terms(args.terms_folder)

enc = encoder.get_encoder(args.model_name, models_dir)
hparams = model.default_hparams()
with open(os.path.join(models_dir, args.model_name, 'hparams.json')) as f:
    hparams.override_from_dict(json.load(f))

tf.compat.v1.disable_eager_execution()
sess = tf.Session()
context = tf.placeholder(tf.int32, [args.batch_size, None])
np.random.seed(args.seed)
tf.set_random_seed(args.seed)
output = sample.sample_sequence(
    hparams=hparams, length=args.length,
    context=context,
    batch_size=args.batch_size,
    temperature=args.temperature, top_k=args.top_k, top_p=args.top_p
)

saver = tf.train.Saver()
ckpt = tf.train.latest_checkpoint(os.path.join(models_dir, args.model_name))
saver.restore(sess, ckpt)

if __name__ == "__main__":
    while True:
        question = input("Question: ")
        answer = input("Answer: ")
        valid_summary_found = False
        attempts = 0

        while not valid_summary_found and attempts < args.max_batches_per_qa:
            summaries_batch = summarize(question, answer)
            for summary in summaries_batch:
                summary_text = summary['summary']
                summary_valid = summary['summary_valid']
                reason = summary['reason']
                if args.print_all:
                    print("Summary: {} | Passed check: {} ({})".format(summary_text, summary_valid, reason))
                    print("---------------------------")
                    if summary_valid:
                        break
                elif summary_valid:
                    valid_summary_found = True
                    print("Summary: {}".format(summary_text))
                    print("---------------------------")
                    break
                    if summary_valid:
                        break

