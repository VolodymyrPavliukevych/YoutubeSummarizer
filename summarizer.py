'''
Name: Volodymyr Pavliukevych
@VolodymyrPavliukevych
run with python3

python summarizer.py --youtubeID 9ofGRzpTtHw
'''

from __future__ import unicode_literals

import argparse
import sys
from timeit import default_timer as timer
import wave
import numpy as np
import tensorflow as tf
import youtube_dl
import ffmpeg
from deepspeech import Model
import keywords
import settings


# Beam width used in the CTC decoder when building candidate transcriptions
BEAM_WIDTH = 500

# The alpha hyperparameter of the CTC decoder. Language Model weight
LM_WEIGHT = 1.50

# Valid word insertion weight. This is used to lessen the word insertion penalty
# when the inserted word is part of the vocabulary
VALID_WORD_COUNT_WEIGHT = 2.10


# These constants are tied to the shape of the graph used (changing them changes
# the geometry of the first layer), so make sure you use the same constants that
# were used during training

# Number of MFCC features to use
N_FEATURES = 26

# Size of the context window used for producing timesteps in the input vector
N_CONTEXT = 9

# Network Parameters
DEFAULT_SEED = 123

def download(youtube_id, crop_time=None):
    "Function description"

    np.random.seed(DEFAULT_SEED)
    tf.set_random_seed(DEFAULT_SEED)
    url = 'https://www.youtube.com/watch?v=' + youtube_id
    output_file_name = 'result-' + youtube_id + '.wav'
    with youtube_dl.YoutubeDL(settings.DOWNLOAD_OPTIONS) as ydl:
        ydl.download([url])
        if crop_time is None:
            _ = ffmpeg.input(youtube_id + '.wav').output(output_file_name, ac=1, ar='16k').overwrite_output().run(capture_stdout=False)
        else:
            _ = ffmpeg.input(youtube_id + '.wav').output(output_file_name, ac=1, t=crop_time, ar='16k').overwrite_output().run(capture_stdout=False)

    return output_file_name

def main():
    "Launch point"

    parser = argparse.ArgumentParser()
    parser.add_argument('--youtube-id', action="store", help="Provide youtube video ID")
    parser.add_argument('--model', required=True, help='Path to the model (protocol buffer binary file)')
    parser.add_argument('--alphabet', required=True, help='Path to the configuration file specifying the alphabet used by the network')
    parser.add_argument('--lm', nargs='?', help='Path to the language model binary file')
    parser.add_argument('--trie', nargs='?', help='Path to the language model trie file created with native_client/generate_trie')
    parser.add_argument('--crop-time', type=int, help='You could process only n seconds.')
    args = parser.parse_args()
    file_name = download(args.youtube_id, crop_time=args.crop_time)
    print('Loading model from file {}'.format(args.model), file=sys.stderr)
    model_load_start = timer()
    deepspeech = Model(args.model, N_FEATURES, N_CONTEXT, args.alphabet, BEAM_WIDTH)
    model_load_end = timer() - model_load_start
    print('Loaded model in {:.3}s.'.format(model_load_end), file=sys.stderr)
    if args.lm and args.trie:
        print('Loading language model from files {} {}'.format(args.lm, args.trie), file=sys.stderr)
        lm_load_start = timer()
        deepspeech.enableDecoderWithLM(args.alphabet, args.lm, args.trie, LM_WEIGHT, VALID_WORD_COUNT_WEIGHT)
        lm_load_end = timer() - lm_load_start
        print('Loaded language model in {:.3}s.'.format(lm_load_end), file=sys.stderr)

    fin = wave.open(file_name, 'rb')
    framerate_sample = fin.getframerate()
    if framerate_sample != 16000:
        print('Warning: original sample rate ({}) is different than 16kHz. Resampling might produce erratic speech recognition.'.format(framerate_sample), file=sys.stderr)
        fin.close()
        return
    else:
        audio = np.frombuffer(fin.readframes(fin.getnframes()), np.int16)

    audio_length = fin.getnframes() * (1/16000)
    fin.close()

    print('Running inference.', file=sys.stderr)
    inference_start = timer()
    result_sub = deepspeech.stt(audio, framerate_sample)
    result = " ".join(filter(lambda word: len(word) < 15, result_sub.split(" ")))
    print("Building top 20 keywords...")
    keyphrases = keywords.extract_keyphrases(result)
    print(keyphrases)
    print("Building summary sentence...")
    print(keywords.extract_summary_sentence(result))

    inference_end = timer() - inference_start
    print('Inference took %0.3fs for %0.3fs audio file.' % (inference_end, audio_length), file=sys.stderr)

if __name__ == '__main__':
    main()
