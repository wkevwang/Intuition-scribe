"""
Generates keywords list from SNOMED CT files
"""

import argparse
import pandas as pd
import os
import re
from utilities import *

parser = argparse.ArgumentParser()
parser.add_argument("--concept_file", type=str, required=True)
parser.add_argument("--description_file", type=str, required=True)
args = parser.parse_args()

def remove_parentheses_text(text):
    return re.sub(r'\(.+?\)', '', text).strip()

df_concept = pd.read_csv(args.concept_file, delimiter='\t')
df_description = pd.read_csv(args.description_file, delimiter='\t')

df_concept_active = df_concept[df_concept['active'] == 1]
df_joined = pd.merge(df_concept_active, df_description, left_on='id', right_on='conceptId')
df_joined_en = df_joined[df_joined['languageCode'] == 'en']

df_findings = df_joined_en[df_joined_en['term'].str.contains('(finding)', regex=False, na=False)].copy()
df_disorders = df_joined_en[df_joined_en['term'].str.contains('(disorder)', regex=False, na=False)].copy()
df_procedures = df_joined_en[df_joined_en['term'].str.contains('(procedure)', regex=False, na=False)].copy()

# Expand synonyms
# df_findings_all = df_joined_en[df_joined_en['conceptId'].isin(df_findings['conceptId'])]
# df_disorders_all = df_joined_en[df_joined_en['conceptId'].isin(df_disorders['conceptId'])]
df_findings_all = df_findings
df_disorders_all = df_disorders
df_procedures_all = df_joined_en[df_joined_en['conceptId'].isin(df_procedures['conceptId'])].copy()

df_findings_all['term'] = df_findings_all['term'].apply(remove_parentheses_text)
df_disorders_all['term'] = df_disorders_all['term'].apply(remove_parentheses_text)
df_procedures_all['term'] = df_procedures_all['term'].apply(remove_parentheses_text)

df_findings_and_disorders = pd.concat([df_findings_all, df_disorders_all], axis=0)
df_findings_and_disorders = df_findings_and_disorders.drop_duplicates('term')
df_procedures_all = df_procedures_all.drop_duplicates('term')

terms_findings_and_disorders = set(df_findings_and_disorders['term'].values.tolist())
terms_procedures = set(df_procedures_all['term'].values.tolist())

with open('findings_and_disorders_terms.txt', 'w') as f:
    for term in terms_findings_and_disorders:
        f.write('{}\n'.format(term))

with open('procedures_terms.txt', 'w') as f:
    for term in terms_procedures:
        f.write('{}\n'.format(term))
