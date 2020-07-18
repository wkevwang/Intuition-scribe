import docx
import argparse
import os
import json
import unidecode
from utilities import *

parser = argparse.ArgumentParser()
parser.add_argument("--file", type=str, required=True)
args = parser.parse_args()

category_colours = {
    "ED7D31": "Clinical Status",
    "FF0000": "Mobility",
    "70AD47": "Nutrition",
    "0070C0": "Toileting",
    "7030A0": "Behaviour",
    "4472C4": "Toileting",
    "00B0F0": "Toileting",
    "00B050": "Nutrition",
}

doc = docx.Document(args.file)

summary = {}
summary_for_date = {}

current_date = None

def clean_text(text):
    text = text.replace('&nbsp;', ' ')
    text = unidecode.unidecode(text)
    text = text.encode('ascii', 'ignore').decode() # Removes unicode characters: https://stackoverflow.com/questions/15321138/removing-unicode-u2026-like-characters-in-a-string-in-python2-7
    text = text.strip(' ,:-')
    return text


# Add all dates to summary
for idx, paragraph in enumerate(doc.paragraphs):
    text = paragraph.text
    text = text.replace('1st', '1')
    text = text.replace('2nd', '2')
    text = text.replace('3rd', '3')
    if is_date(text):
        summary[text] = {category: [] for category in category_colours.values()}
        current_date = text
    last_colour = None
    for run in paragraph.runs:
        for colour, category in category_colours.items():
            if run.font.color.rgb == docx.shared.RGBColor.from_string(colour):
                cleaned_text = clean_text(run.text)
                if docx.shared.RGBColor.from_string(colour) == last_colour:
                    summary[current_date][category][-1] += ' ' + cleaned_text
                else:
                    summary[current_date][category].append(cleaned_text)
        last_colour = run.font.color.rgb
    # Postprocessing
    for colour, category in category_colours.items():
        processed_text = []
        for text in summary[current_date][category]:
            split_text = text.split('.')
            cleaned_split_text = [capitalize(clean_text(t)) for t in split_text]
            processed_text += cleaned_split_text
        summary[current_date][category] = processed_text


with open(os.path.splitext(args.file)[0] + '.json', 'w') as f:
    json.dump(summary, f, indent=4)
