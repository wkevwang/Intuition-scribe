"""
Transcribe an audio file stored in Google Cloud Storage
with Google Speech-to-Text.

Access Google Storage with Menu->Storage->intuition-transcripts

The 'video' model performs much better than other models.
"""


from google.cloud import speech_v1p1beta1 as speech
import argparse
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'gc_key.json')
client = speech.SpeechClient()

parser = argparse.ArgumentParser()
parser.add_argument("--uri", type=str, required=True)
args = parser.parse_args()

audio = speech.types.RecognitionAudio(uri=args.uri)

config = speech.types.RecognitionConfig(
    encoding=speech.enums.RecognitionConfig.AudioEncoding.MP3,
    sample_rate_hertz=44100,
    language_code='en-US',
    enable_automatic_punctuation=True,
    enable_word_time_offsets=True,
    use_enhanced=True,
    model='video')

print('Waiting for operation to complete...')
operation = client.long_running_recognize(config, audio)

response = operation.result(timeout=240)

# The transcript within each result is separate and sequential per result.
# However, the words list within an alternative includes all the words
# from all the results thus far. Thus, to get all the words with speaker
# tags, you only have to take the words list from the last result:
result = response.results[-1]

# words_info = result.alternatives[0].words

# # Printing out the output:
# for word_info in words_info:
#     print(u"word: '{}', speaker_tag: {}".format(
#         word_info.word, word_info.speaker_tag))

for result in response.results:
    # The first alternative is the most likely one for this portion.
    print(u'Transcript: {}'.format(result.alternatives[0].transcript))
    print('Confidence: {}'.format(result.alternatives[0].confidence))

# for result in response.results:
#     alternative = result.alternatives[0]
#     print(u'Transcript: {}'.format(alternative.transcript))
#     print('Confidence: {}'.format(alternative.confidence))
#     for word_info in alternative.words:
#         word = word_info.word
#         start_time = word_info.start_time
#         end_time = word_info.end_time
#         print('Word: {}, start_time: {}, end_time: {}'.format(
#             word,
#             start_time.seconds + start_time.nanos * 1e-9,
#             end_time.seconds + end_time.nanos * 1e-9))
