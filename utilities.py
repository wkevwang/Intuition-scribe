from datetime import datetime

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
