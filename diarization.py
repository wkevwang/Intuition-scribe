from resemblyzer import preprocess_wav, VoiceEncoder
import argparse
import json
import os

parser = argparse.ArgumentParser()
parser.add_argument("--audio_file", type=str, required=True)
parser.add_argument("--doctor_segments", type=str, nargs='+', required=True)
parser.add_argument("--patient_segments", type=str, nargs='+', required=True)
parser.add_argument("--partials_n_frames", default=160, type=int, required=False)
args = parser.parse_args()

time_per_partial_frame = args.partials_n_frames * 10 / 1000 * 16000
wav = preprocess_wav(args.audio_file)

num_doctor_segments = len(args.doctor_segments)
num_patient_segments = len(args.patient_segments)
doctor_segments = [[float(time.split('-')[0]), float(time.split('-')[1])]
                    for time in args.doctor_segments]
patient_segments = [[float(time.split('-')[0]), float(time.split('-')[1])]
                    for time in args.patient_segments]

# Cut some segments from single speakers as reference audio
segments = doctor_segments + patient_segments
speaker_names = (["Doctor"] * num_doctor_segments) + (["Patient"] * num_patient_segments)
speaker_wavs = [wav[int(s[0] * sampling_rate):int(s[1]) * sampling_rate] for s in segments]

rate = 16
encoder = VoiceEncoder("cpu")
print("Running the continuous embedding on cpu, this might take a while...")
_, cont_embeds, wav_splits = encoder.embed_utterance(wav, return_partials=True, rate=rate)

speaker_embeds = [encoder.embed_utterance(speaker_wav) for speaker_wav in speaker_wavs]
similarity_dict = {name: cont_embeds @ speaker_embed for name, speaker_embed in 
                zip(speaker_names, speaker_embeds)}
similarity_matrix = np.array([cont_embeds @ speaker_embed for name, speaker_embed in
                            zip(speaker_names, speaker_embeds)])

speaker_predictions_indexes = np.argmax(similarity_matrix, axis=0)
speaker_predictions = [speaker_names[index] for index in speaker_predictions_indexes]
times_per_sec = 2
interval = int(rate / times_per_sec)
for i in range(0, len(speaker_predictions), interval):
    seconds = i * (960 / 16000)
    seconds += time_per_partial_frame / 2 / 16000 # Centre prediction at middle of interval
    print("{}m:{}s | Speaker: {} | Doctor Conf: {}".format(int(seconds / 60), round(seconds % 60, 1), speaker_predictions[i], similarity_matrix[0, i]))

output_json = {
    "diarization": []
}
# Produce output JSON data
for i in range(len(speaker_predictions)):
    seconds = i * (960 / 16000)
    seconds += time_per_partial_frame / 2 / 16000 # Centre prediction at middle of interval
    seconds = round(seconds, 2)
    speaker_prediction = speaker_predictions[i]
    output_json["diarization"].append({
        "time": seconds,
        "speaker": speaker_prediction
    })

filename_prefix = os.path.splitext(os.path.basename(args.audio_file))[0]
json_filename = filename_prefix + '-diarization.json'
with open(json_filename, 'w') as f:
    json.dump(output_json, f, indent=4)
