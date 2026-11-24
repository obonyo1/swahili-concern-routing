import os
import re
import pandas as pd

RAW_DIR = 'data/raw'
OUT_FILE = 'data/annotated/safety_candidates.csv'
FILES = ['HABARI_Cleaned.txt', 'MITANDAO_Cleaned.txt', 'SHERIA_Cleaned.txt']
KEYWORDS = ['wizi', 'wezi', 'ujambazi', 'jambazi', 'majambazi', 'uhalifu',
            'mhalifu', 'wahalifu', 'polisi', 'vurugu', 'mauaji', 'kuuawa',
            'ubakaji', 'kubakwa', 'bunduki', 'kisu']
MIN_CHARS, MAX_CHARS, PER_FILE = 10, 300, 2000

pattern = re.compile('|'.join(KEYWORDS))
rows = []

for name in FILES:
    path = os.path.join(RAW_DIR, name)
    if not os.path.exists(path):
        print(f'Missing {path}, skipping')
        continue
    scanned = hits = 0
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not MIN_CHARS <= len(line) <= MAX_CHARS:
                continue
            scanned += 1
            match = pattern.search(line.lower())
            if match:
                hits += 1
                rows.append({'sentence': line, 'source': name, 'keyword': match.group()})
    print(f'{name}: {hits:,} hits in {scanned:,} usable lines ({hits / max(scanned, 1):.2%})')

if not rows:
    raise SystemExit('No candidates found. Check data/raw and the keyword list.')

df = pd.DataFrame(rows).drop_duplicates(subset='sentence')
parts = [g.sample(min(len(g), PER_FILE), random_state=42) for _, g in df.groupby('source')]
df = pd.concat(parts, ignore_index=True)

os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
df.to_csv(OUT_FILE, index=False, encoding='utf-8')
print(df['source'].value_counts())
print(f'Saved {len(df):,} candidates to {OUT_FILE}')
