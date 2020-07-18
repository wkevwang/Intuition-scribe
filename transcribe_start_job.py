import boto3

client = boto3.client('transcribe')

response = client.start_medical_transcription_job(
    MedicalTranscriptionJobName="Medical-Transcription-Job-MzoeBJyVlE0-Speakers",
    LanguageCode='en-US',
    MediaFormat='mp3',
    Media={
        'MediaFileUri': "s3://emr-storage-100/conversation-MzoeBJyVlE0.mp3"
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