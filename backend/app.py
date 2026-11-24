import os
import time
import uuid

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

import db
import ml

load_dotenv()

VILLAGES = ['Mathare 4A', 'Mathare North', 'Kosovo', 'Mabatini', 'Huruma']
AUDIO_TYPES = {'.m4a', '.mp4', '.wav', '.3gp', '.aac', '.webm', '.mp3', '.caf'}
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024
CORS(app)


def elapsed_ms(start):
    return round((time.perf_counter() - start) * 1000)


@app.get('/health')
def health():
    return jsonify(status='running', model=ml.config['selected_model'],
                   classes=ml.classes, threshold=ml.threshold)


@app.get('/api/categories')
def categories():
    return jsonify(categories=ml.classes)


@app.get('/api/villages')
def villages():
    return jsonify(villages=VILLAGES)


@app.post('/api/classify')
def classify_text():
    text = ((request.get_json(silent=True) or {}).get('text') or '').strip()
    if not text:
        return jsonify(error='text is required'), 400
    return jsonify(ml.classify(text))


@app.post('/api/submit')
def submit():
    started = time.perf_counter()
    village = (request.form.get('village') or '').strip() or None
    text = (request.form.get('text') or '').strip()
    audio = request.files.get('audio')
    timings = {}

    if audio:
        ext = os.path.splitext(audio.filename or '')[1].lower()
        path = os.path.join(UPLOAD_DIR, uuid.uuid4().hex + (ext if ext in AUDIO_TYPES else '.m4a'))
        audio.save(path)
        step = time.perf_counter()
        try:
            text = ml.transcribe(path)
        except Exception as error:
            return jsonify(error=f'Transcription failed: {error}'), 502
        finally:
            os.remove(path)
        timings['transcribe_ms'] = elapsed_ms(step)

    if not text:
        return jsonify(error='No speech detected and no text provided'), 400

    step = time.perf_counter()
    result = ml.classify(text)
    timings['classify_ms'] = elapsed_ms(step)

    saved = db.save_concern(text, result['category'], result['confidence'], result['flagged'], village)
    timings['total_ms'] = elapsed_ms(started)

    return jsonify(id=saved['concern_id'], transcript=text, village=village,
                   timings=timings, **result), 201


@app.get('/api/concerns')
def concerns():
    limit = min(request.args.get('limit', 50, type=int), 200)
    return jsonify(concerns=db.list_concerns(
        category=request.args.get('category') or None,
        village=request.args.get('village') or None,
        flagged_only=request.args.get('flagged') == 'true',
        limit=limit))


@app.get('/api/stats')
def stats():
    return jsonify(db.stats())


if __name__ == '__main__':
    if os.getenv('WARM_UP', '1') == '1':
        ml.warm_up()
    app.run(host='0.0.0.0', port=int(os.getenv('FLASK_PORT', 5000)))
