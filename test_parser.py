import json
import os
import re

import pandas as pd
from bs4 import BeautifulSoup


def load_metadata(deputies_path: str) -> pd.DataFrame:
    """
    Load deputies metadata into a DataFrame. Supports CSV and TSV.
    Ensures a 'name' column and converts NaN to None for JSON.
    """
    if deputies_path.lower().endswith('.tsv'):
        df = pd.read_csv(deputies_path, sep='\t')
    else:
        df = pd.read_csv(deputies_path)
    if 'name' not in df.columns:
        for col in ['firstLastName', 'Speaker_name', 'speaker']:
            if col in df.columns:
                df['name'] = df[col]
                break
        else:
            raise KeyError(f"Brak kolumny 'name' w metadanych. Dostępne kolumny: {list(df.columns)}")
    df = df.where(pd.notnull(df), None)
    return df


def parse_speech_file(transcript_dir: str, base: str, idx: str) -> str:
    """
    Load individual speech HTML and return its full text as a single cleaned line.
    """
    path = os.path.join(transcript_dir, f"{base}_{int(idx)}.html")
    if not os.path.exists(path):
        return ''
    with open(path, encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    header = soup.find('h2', class_='mowca')
    if not header:
        return ''
    segments = []
    for sib in header.find_next_siblings():
        if sib.name == 'h2':
            break
        if sib.name == 'p':
            text = sib.get_text(separator=' ', strip=True)
            if text:
                segments.append(text)
    full = ' '.join(segments)
    # collapse whitespace
    return re.sub(r"\s+", ' ', full).strip()


def process_html_transcripts(transcript_dir: str, deputies_path: str, output_dir: str):
    """
    Reads backbone _0.html sequentially. Outputs combined.txt with lines:
    uniqueId<TAB>text for contexts and speeches, preserving document order.
    Contexts and speeches share a unified numeric key sequence. Contexts are merged per block.
    Also outputs metadata JSON for speeches.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Identify backbone file
    htmls = [f for f in os.listdir(transcript_dir) if f.lower().endswith('.html')]
    backbone = next((f for f in htmls if f.endswith('_0.html')), None)
    if not backbone:
        raise FileNotFoundError('Brak backbone *_0.html')
    base = backbone[:-7]
    soup0 = BeautifulSoup(open(os.path.join(transcript_dir, backbone), encoding='utf-8'), 'html.parser')

    metadata_df = load_metadata(deputies_path)
    combined = []
    metadata_list = []
    seq = 1
    buffer_context = []

    def flush_context():
        nonlocal seq, buffer_context
        if buffer_context:
            merged = ' '.join(buffer_context)
            clean = re.sub(r"\s+", ' ', merged).strip()
            uid = f"{base}_{seq}"
            combined.append(f"{uid}\t{clean}")
            metadata_list.append({'id': uid, 'speaker': None, 'metadata': []})
            seq += 1
            buffer_context.clear()

    # Traverse paragraphs in backbone
    for p in soup0.find_all('p'):
        if 'mowca-link' in (p.get('class') or []):
            # flush context
            flush_context()
            # inject speech
            a = p.find('a', attrs={'name': True})
            if not a:
                continue
            idx = a['name']
            speaker = a.get_text(strip=True)
            speech = parse_speech_file(transcript_dir, base, idx)
            clean_speech = re.sub(r"\s+", ' ', speech).strip()
            uid = f"{base}_{seq}"
            combined.append(f"{uid}\t{clean_speech}")
            rows = metadata_df[metadata_df['name'].apply(lambda n: n and n in speaker)]
            recs = rows.to_dict(orient='records')
            metadata_list.append({'id': uid, 'speaker': speaker, 'metadata': recs})
            seq += 1
        else:
            # accumulate context text
            text = p.get_text(separator=' ', strip=True)
            if text:
                buffer_context.append(text)

    # final flush
    flush_context()

    # write combined file
    out_txt = os.path.join(output_dir, f"{base}_combined.txt")
    with open(out_txt, 'w', encoding='utf-8') as f:
        for line in combined:
            f.write(line + '\n')

    # write metadata JSON
    out_meta = os.path.join(output_dir, f"{base}_metadata.json")
    with open(out_meta, 'w', encoding='utf-8') as f:
        json.dump(metadata_list, f, ensure_ascii=False, indent=2)


# Przykład wywołania funkcji bez argparse:
if __name__ == '__main__':
    process_html_transcripts(
        transcript_dir='data/transcripts/10/1',
        deputies_path='data/deputies/10/deputies.csv',
        output_dir='output'
    )
