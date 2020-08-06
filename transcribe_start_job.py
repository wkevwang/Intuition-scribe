import boto3
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument("--path", type=str, required=True)
parser.add_argument("--type", type=str, default='medical', required=False)
parser.add_argument("--lang", type=str, default='en-US', required=False)
args = parser.parse_args()

client = boto3.client('transcribe')

if args.type == 'medical':
    response = client.start_medical_transcription_job(
        MedicalTranscriptionJobName="Medical-Transcription-Job-" + os.path.basename(args.path).split('.')[0] + '_' + args.lang,
        LanguageCode=args.lang,
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
else:
    response = client.start_transcription_job(
        TranscriptionJobName="Transcription-Job-" + os.path.basename(args.path).split('.')[0] + '_' + args.lang,
        LanguageCode=args.lang,
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
    )