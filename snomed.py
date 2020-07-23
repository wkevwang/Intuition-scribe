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
df_events = df_joined_en[df_joined_en['term'].str.contains('(event)', regex=False, na=False)].copy()
df_products = df_joined_en[df_joined_en['term'].str.contains('(product)', regex=False, na=False)].copy()

# df_findings_all = df_joined_en[df_joined_en['conceptId'].isin(df_findings['conceptId'])] # Expand synonyms
# df_disorders_all = df_joined_en[df_joined_en['conceptId'].isin(df_disorders['conceptId'])] # Expand synonyms
df_findings_all = df_findings # Don't expand synonyms
df_disorders_all = df_disorders # Don't expand synonyms
df_procedures_all = df_joined_en[df_joined_en['conceptId'].isin(df_procedures['conceptId'])].copy() # Expand synonyms
df_events_all = df_joined_en[df_joined_en['conceptId'].isin(df_events['conceptId'])].copy() # Expand synonyms
df_products_all = df_joined_en[df_joined_en['conceptId'].isin(df_products['conceptId'])].copy() # Expand synonyms

df_findings_all['term'] = df_findings_all['term'].apply(remove_parentheses_text)
df_disorders_all['term'] = df_disorders_all['term'].apply(remove_parentheses_text)
df_procedures_all['term'] = df_procedures_all['term'].apply(remove_parentheses_text)
df_events_all['term'] = df_events_all['term'].apply(remove_parentheses_text)
df_products_all['term'] = df_products_all['term'].apply(remove_parentheses_text)

df_findings_all = df_findings_all.drop_duplicates('term')
df_disorders_all = df_disorders_all.drop_duplicates('term')
df_procedures_all = df_procedures_all.drop_duplicates('term')
df_events_all = df_events_all.drop_duplicates('term')
df_products_all = df_products_all.drop_duplicates('term')

terms_findings = list(set(df_findings_all['term'].values.tolist()))
terms_disorders = list(set(df_disorders_all['term'].values.tolist()))
terms_procedures = list(set(df_procedures_all['term'].values.tolist()))
terms_events = list(set(df_events_all['term'].values.tolist()))
terms_products = list(set(df_products_all['term'].values.tolist()))

terms_findings.sort(key=len, reverse=True)
terms_disorders.sort(key=len, reverse=True)
terms_procedures.sort(key=len, reverse=True)
terms_events.sort(key=len, reverse=True)
terms_products.sort(key=len, reverse=True)

with open('terms/findings_terms.txt', 'w') as f:
    for term in terms_findings:
        f.write('{}\n'.format(term))

with open('terms/disorders_terms.txt', 'w') as f:
    for term in terms_disorders:
        f.write('{}\n'.format(term))

with open('terms/procedures_terms.txt', 'w') as f:
    for term in terms_procedures:
        f.write('{}\n'.format(term))

with open('terms/events_terms.txt', 'w') as f:
    for term in terms_events:
        f.write('{}\n'.format(term))

with open('terms/products_terms.txt', 'w') as f:
    for term in terms_products:
        f.write('{}\n'.format(term))
