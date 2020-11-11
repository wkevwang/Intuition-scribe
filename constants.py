from colorama import Fore, Style

CC = "Chief Complaint"
HPI = "History of Present Illness"
PMH = "Past Medical History"
PSH = "Past Surgical History"
MEDICATIONS = "Medications"
ALLERGIES = "Allergies"
FH = "Family History"
SH = "Social History"


CATEGORIES = [
    CC, HPI, PMH, PSH, MEDICATIONS, ALLERGIES, FH, SH
]


REGEX_MARKERS = {
    "QUESTION": [r"(?:^|\. |\? |\! )([^\.\?\!]+?\?)"],
    "INFO": [r"(where)", r"(when)", r"(why)", r"(who)", r"(how long)", r"(have you)", r"(is there)"],
    "COMPLAINT": [
        r"(I've been having[^\.\?\!]+(\.|\?|\!))",
        r"(I've had[^\.\?\!]+(\.|\?|\!))",
        r"(I have[^\.\?\!]+(\.|\?|\!))",
        r"(I had[^\.\?\!]+(\.|\?|\!))",
        r"(I got[^\.\?\!]+(\.|\?|\!))"
    ],
    "TIME": [
        r"((every|since|)? ?((couple)|(a few)|(several)|(one)|(two)|(three)|(four)|(five)|(six)|(seven)|(eight)|(nine)|(ten)|\d+)? ?(minutes?|hours?|days?|weeks?|months?|years?) ?(ago|after|before)?)",
    ],
    "CC_CATEGORY": [
        r"(what brings you in today)",
        r"(what('s| has) been going on)",
        r"(what('s| is) going on)",
    ],
    "PMH_CATEGORY": [
        r"(past medical history)",
    ],
    "PSH_CATEGORY": [
        r"(surgeries)"
    ],
    "ALLERGIES_CATEGORY": [
        r"(allergies)",
        r"(allergic)"
    ],
    "MEDICATIONS_CATEGORY": [
        r"(medications)",
        r"(I take[^\.\?\!]+(\.|\?|\!))",
        r"(I took[^\.\?\!]+(\.|\?|\!))",
    ],
    "FH_CATEGORY": [
        r"(family)(?: |\.|\?|\!)",
        r"(family history)(?: |\.|\?|\!)",
        r"(mom and dad)(?: |\.|\?|\!)",
        r"(father)(?: |\.|\?|\!)",
        r"(mother)(?: |\.|\?|\!)",
        r"(mom)(?: |\.|\?|\!)",
        r"(dad)(?: |\.|\?|\!)"
    ],
    "SH_CATEGORY": [
        r"(drug use)",
        r"(tobacco)",
        r"(smoke)",
        r"(smoking)",
        r"(alcohol)",
        r"(coffee)",
        r"(exercise)",
        r"(diet)",
        r"(recreational drugs)",
        r"(relationship status)",
        r"(married)",
    ],
    "NEGATION": [
        r"(?: |^)(no)(?: |\.|\?)"
    ],
}


COLOUR_MAP = {
    "SNOMED_CT": Fore.GREEN,
    "REGEX_QUESTION": Fore.RED,
    "REGEX_INFO": Fore.RED,
    "REGEX_COMPLAINT": Fore.MAGENTA,
    "QUESTION_RESPONSE": Fore.MAGENTA,
    "REGEX_CC_CATEGORY": Fore.CYAN,
    "REGEX_PMH_CATEGORY": Fore.CYAN,
    "REGEX_PSH_CATEGORY": Fore.CYAN,
    "REGEX_ALLERGIES_CATEGORY": Fore.CYAN,
    "REGEX_MEDICATIONS_CATEGORY": Fore.CYAN,
    "REGEX_FH_CATEGORY": Fore.CYAN,
    "REGEX_SH_CATEGORY": Fore.CYAN,
    "REGEX_NEGATION": Fore.MAGENTA,
    "REGEX_TIME": Fore.MAGENTA,
}
