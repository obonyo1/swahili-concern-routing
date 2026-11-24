import json
import os
import re
from functools import lru_cache

import joblib

MODELS_DIR = os.getenv('MODELS_DIR') or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'models')
WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'small')

with open(os.path.join(MODELS_DIR, 'model_config.json')) as f:
    config = json.load(f)

classes = config['classes']
threshold = float(config['confidence_threshold'])
classifier = joblib.load(os.path.join(MODELS_DIR, 'selected_model.pkl'))


def normalise(text):
    text = re.sub(r'[^\w\s]', ' ', str(text).lower())
    return re.sub(r'\s+', ' ', text).strip()


@lru_cache(maxsize=1)
def _encoder():
    import torch
    from transformers import AutoModel, AutoTokenizer

    name = config['embedding_model']
    return torch, AutoTokenizer.from_pretrained(name), AutoModel.from_pretrained(name).eval()


@lru_cache(maxsize=1)
def _whisper():
    import whisper

    return whisper.load_model(WHISPER_MODEL)


def embed_texts(texts):
    torch, tokenizer, model = _encoder()
    if config['normalise']:
        texts = [normalise(t) for t in texts]
    batch = tokenizer(texts, return_tensors='pt', padding=True,
                      truncation=True, max_length=config['max_length'])
    with torch.no_grad():
        hidden = model(**batch).last_hidden_state
    mask = batch['attention_mask'].unsqueeze(-1).float()
    return ((hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)).numpy()


def classify(text):
    proba = classifier.predict_proba(embed_texts([text]))[0]
    best = int(proba.argmax())
    confidence = float(proba[best])
    return {'category': classes[best], 'confidence': round(confidence, 4),
            'flagged': confidence < threshold}


def transcribe(path):
    return _whisper().transcribe(path, language='sw', fp16=False)['text'].strip()


def warm_up():
    _encoder()
    try:
        _whisper()
    except Exception as error:
        print(f'Whisper unavailable, text submissions only: {error}')
