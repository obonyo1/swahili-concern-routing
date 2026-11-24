import os
import pandas as pd

RAW_DIR = 'data/raw'
ANN_DIR = 'data/annotated'
SAFETY_FILE = os.path.join(ANN_DIR, 'safety_validated.csv')
OUT_FILE = os.path.join(ANN_DIR, 'labelled_concerns.csv')

FILES = {
    'Health': 'AFYA_Cleaned.txt',
    'Food Security': 'KILIMO_Cleaned.txt',
    'Education': 'ELIMU_Cleaned.txt',
}
MIN_CHARS, MAX_CHARS = 10, 300
PER_CLASS = 2000
SEED = 42


def read_lines(filename, label):
    with open(os.path.join(RAW_DIR, filename), encoding='utf-8') as f:
        lines = [line.strip() for line in f]
    lines = [l for l in lines if MIN_CHARS <= len(l) <= MAX_CHARS and not l.isdigit()]
    print(f'{label}: {len(lines):,} usable lines')
    return pd.DataFrame({'sentence': lines, 'label': label, 'source': filename})


frames = [read_lines(name, label) for label, name in FILES.items()]

if os.path.exists(SAFETY_FILE):
    safety = pd.read_csv(SAFETY_FILE)[['sentence']]
    safety['label'] = 'Safety'
    safety['source'] = 'safety_validated.csv'
    frames.append(safety)
else:
    print('No safety_validated.csv found, building without Safety')

df = pd.concat(frames, ignore_index=True)
df['sentence'] = df['sentence'].str.strip()
df = df.drop_duplicates(subset=['sentence', 'label'])

conflicts = df[df.duplicated(subset='sentence', keep=False)]
df = df.drop(conflicts.index)
print(f'Removed {len(conflicts)} rows with conflicting labels')

n = min(df['label'].value_counts().min(), PER_CLASS)
df = df.groupby('label').sample(n=n, random_state=SEED)
df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)

os.makedirs(ANN_DIR, exist_ok=True)
df.to_csv(OUT_FILE, index=False, encoding='utf-8')
print(df['label'].value_counts())
print(f'Saved {len(df):,} rows to {OUT_FILE}')
