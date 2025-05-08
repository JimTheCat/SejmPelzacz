import json
import os

from bs4 import BeautifulSoup


def load_session_metadata(base_path, kadencja, posiedzenie, date_str):
    """
    Wczytuje plik JSON z metadanymi dla danego posiedzenia.
    """
    json_path = os.path.join(base_path, str(kadencja), str(posiedzenie), f"{date_str}.json")
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_main_html(base_path, kadencja, posiedzenie, date_str):
    """
    Parsuje główny plik HTML posiedzenia ({date_str}_0.html), zwracając całą treść
    dla wypowiedzi nr 0 (przebieg posiedzenia).
    """
    html_path = os.path.join(base_path, str(kadencja), str(posiedzenie), f"{date_str}_0.html")
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    content = []
    for tag in soup.find_all(['p', 'h1', 'h2', 'blockquote']):
        # Przerywamy po napotkaniu linku do pierwszego mówcy
        if tag.name == 'p' and tag.find('a', attrs={'name': True}):
            break
        content.append(tag.get_text(strip=True))
    return "\n".join(content)


def parse_speaker_html(base_path, kadencja, posiedzenie, date_str, num):
    """
    Parsuje plik HTML dla konkretnego mówcy ({date_str}_{num}.html)
    i zwraca czysty tekst jego wypowiedzi.
    """
    html_path = os.path.join(base_path, str(kadencja), str(posiedzenie), f"{date_str}_{num}.html")
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    paragraphs = []
    mowca_tag = soup.find('h2', class_='mowca')
    if mowca_tag:
        for sib in mowca_tag.find_next_siblings():
            if sib.name == 'h2':
                break
            if sib.name == 'p':
                paragraphs.append(sib.get_text(strip=True))
    return "\n".join(paragraphs)


def process_transcript(base_path, kadencja, posiedzenie):
    """
    Przetwarza całe posiedzenie, zwraca listę słowników z metadanymi i tekstem każdej wypowiedzi.
    """

    folder = os.path.join(base_path, str(kadencja), str(posiedzenie))
    json_files = [f for f in os.listdir(folder) if f.endswith('.json')]
    if not json_files:
        raise FileNotFoundError("Nie znaleziono pliku JSON z metadanymi posiedzenia")
    date_str = os.path.splitext(json_files[0])[0]

    metadata = load_session_metadata(base_path, kadencja, posiedzenie, date_str)
    statements = metadata.get('statements', [])

    results = []
    for st in statements:
        num = st.get('num')
        if num is None:
            continue
        if num == 0:
            text = parse_main_html(base_path, kadencja, posiedzenie, date_str)
        else:
            text = parse_speaker_html(base_path, kadencja, posiedzenie, date_str, num)
        entry = {
            'num': num,
            'name': st.get('name'),
            'function': st.get('function'),
            'start': st.get('startDateTime'),
            'end': st.get('endDateTime'),
            'text': text
        }
        results.append(entry)
    return results


if __name__ == '__main__':
    base = 'data/transcripts'
    kadencja = 10
    posiedzenie = 1
    transcript = process_transcript(base, kadencja, posiedzenie)
    for entry in transcript:
        print(f"# Wypowiedź {entry['num']} - {entry['name']}")
        print(entry['text'])
        print("\n---\n")
