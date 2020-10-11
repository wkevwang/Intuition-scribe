"""
Sends audio file to rev.ai and gets transcript file back.
"""

import argparse
import os
import json
from time import sleep
from rev_ai import apiclient, JobStatus

from utilities import prp

ACCESS_TOKEN = "028REO2rLmJ-wBANOuNEtsRy6E14glwUPKHc5uqmG4CfW6Ny7Lmsdjnn4OMgC91l2LdiL97gf7haiNu6lMv2ss_P2d8K8"
client = apiclient.RevAiAPIClient(ACCESS_TOKEN)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio_file", type=str, required=True)
    parser.add_argument("--output_folder", type=str, required=True)
    args = parser.parse_args()

    job = client.submit_job_local_file(
        args.audio_file,
        skip_diarization=True)
    
    job_details = client.get_job_details(job.id)

    print("Waiting for transcription...")
    while job_details.status is not JobStatus.TRANSCRIBED:
        sleep(1)
        job_details = client.get_job_details(job.id)
    
    transcript_json = client.get_transcript_json(job.id)

    filename_prefix = os.path.splitext(os.path.basename(args.audio_file))[0]
    filename = filename_prefix + '_rev_transcript.json'
    with open(os.path.join(args.output_folder, filename), 'w') as f:
        json.dump(transcript_json, f, indent=4)
