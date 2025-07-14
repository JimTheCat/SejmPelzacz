'''
Sejm Crawler
'''

# This script is a web crawler that scrapes data from the Polish Sejm website.

import os

from test_parser import process_html_transcripts

# Sprawdzenie istnienia folderu 'data'
if not os.path.exists('data'):
    os.makedirs('data')
    os.makedirs('data/terms')
    os.makedirs('data/deputies')
    os.makedirs('data/transcripts')


def transcripts_process():
    for kadencja_dir in os.listdir('data/transcripts'):
        kadencja_path = os.path.join('data/transcripts', kadencja_dir)
        if os.path.isdir(kadencja_path):
            for posiedzenie_dir in os.listdir(kadencja_path):
                transcript_dir = os.path.join(kadencja_path, posiedzenie_dir)
                if os.path.isdir(transcript_dir):
                    deputies_path = os.path.join('data/deputies', kadencja_dir, 'deputies.csv')
                    if os.path.exists(deputies_path):
                        htmls = [f for f in os.listdir(transcript_dir) if f.endswith('_0.html')]
                        if htmls:
                            base = htmls[0][:-7]  # YYYY-MM-DD
                            year = base[:4]
                            output_dir = os.path.join('output', year)
                            process_html_transcripts(transcript_dir, deputies_path, output_dir)

if __name__ == '__main__':
    # download_all_terms()
    # download_transcripts()
    # download_deputies()
    transcripts_process()
