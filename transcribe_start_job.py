import boto3
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument("--path", type=str, required=True)
args = parser.parse_args()

client = boto3.client('transcribe')

response = client.start_medical_transcription_job(
    MedicalTranscriptionJobName="Medical-Transcription-Job-" + os.path.basename(args.path).split('.')[0],
    LanguageCode='en-US',
    MediaFormat='mp3',
    Media={
        'MediaFileUri': args.path
    },
    OutputBucketName="emr-storage-100",
    Settings={
        'ShowSpeakerLabels': True,
        'MaxSpeakerLabels': 2,
        'ShowAlternatives': True,
        'MaxAlternatives': 2,
    },
    Specialty='PRIMARYCARE',
    Type='CONVERSATION',
)