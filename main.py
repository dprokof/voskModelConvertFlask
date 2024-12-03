import os
import io
import wave
import json
from typing import Tuple, List, Dict, Any
from flask import Flask, request, jsonify
from vosk import Model,KaldiRecognizer
from pydub import AudioSegment

app = Flask(__name__)

vosk_model = Model('/home/dprokof/PycharmProjects/voskModelConvertFlask/vosk-model-small-ru-0.22')


def convert_mp3_to_wav(path: str) -> str:
    audio = AudioSegment.from_mp3(path)
    wav_path = "temp.wav"
    audio.export(wav_path, format="wav")
    return wav_path


def speech(path: str) -> tuple[list[dict[str, int | str | None | bool | Any]], dict[str, int]]:
    wf = wave.open(path, 'rb')
    rec = KaldiRecognizer(vosk_model, wf.getframerate())

    dialog = []
    result = {"receiver": 0, "transmitter": 0}
    speaker = None
    start = 0
    voice = False
    gender = None

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            res = rec.Result()
            res_json = json.loads(res)

            if "text" in res_json:
                text = res_json("text")
                if "receiver" in text.lower():
                    speaker = "receiver"
                elif "transmitter" in text.lower():
                    speaker = "transmitter"

                voice = '!' in text
                gender = "male" if speaker == "receiver" else "female"
                dialog.append({
                    "source": speaker,
                    "text": text,
                    "duration": 5,
                    "raised_voice": voice,
                    "gender": gender
                })

    return dialog, result


@app.route('/asr', methods=['POST'])
def asr():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    file_path = os.path.join("uploads", file.filename)
    file.save(file_path)

    wav_path = convert_mp3_to_wav(file_path)

    dialog, result = speech(wav_path)

    response = {
        'dialog': dialog,
        'result_duration': result
    }

    return jsonify(response)

if __name__ == "__main__":
    app.run(debug=True)