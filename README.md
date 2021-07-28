# Intuition Scribe
Prototype of an automated medical scribe, done in collaboration with doctors from University of British Columbia and St. Paul's Hospital.

The goal of Intuition Scribe is to automatically produce a [admission note](https://en.wikipedia.org/wiki/Admission_note) from an audio recording of a [patient-doctor interview](https://www.youtube.com/watch?v=9om2tedf9oo).

See this [Figma prototype](https://www.figma.com/proto/rL3K2u8oeqsG0gcuiHLJY1/Intuition-Scribe?node-id=97%3A20&scaling=min-zoom&page-id=0%3A1&starting-point-node-id=337%3A2) for a demo.

## Design
The pipeline follows these stages:
1. **Speech recognition** The audio is converted to text. Currently the best method is to use the Rev.ai speech-to-text API, which also inserts punctuation and capitalization. See [rev_transcription.py](rev_transcription.py) for more details.
2. **Speech diarization** The text is assigned to speakers (either the doctor or patient) to form a dialogue transcript. Currently the [Resemblyzer](https://github.com/resemble-ai/Resemblyzer) library is used, which is based off of [Generalized End-To-End Loss for Speaker Verification](https://arxiv.org/pdf/1710.10467.pdf). This method requires that for each conversation, a snippet of audio from each speaker is fed to the model for calibration. See [diarization.py](diarization.py) for more details.
3. **Question and Answer Summarization** After a transcript is created, the question-answer turns in the dialogue are extracted and then summarized. The question-answer turns are determined from the punctuation (prescence of question marks from the speech recognition). These turns are summarized using T5. This model is trained on a dataset collected from YouTube and labelled by our doctors. See [t5/train_qa_summarizer.py](t5/train_qa_summarizer.py) for more details.
4. **Categorization** The summarized statements are then assigned to sections of the admission note, like Chief Complaint, History of Present Illness, Social History, etc. Current a keyword based assignment is used.

## Requirements
* [SNOMED CT](https://www.snomed.org/) terms file: this library of medical keywords is used for determining which text is medically relevant
* [Huggingface transformers](https://huggingface.co/transformers/) for the T5 model

## Other Experiments
* `coqa/`: using the CoQA dataset for extra training data for the question-answer summarization model
* `gpt/`: using a few-shot tuned GPT2 model for the question-answer summarization model