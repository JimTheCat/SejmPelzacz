'''
Sejm Crawler
'''

# This script is a web crawler that scrapes data from the Polish Sejm website.

import os

from deputies import download_deputies
from transcripts import download_transcripts

# Sprawdzenie istnienia folderu 'data'
if not os.path.exists('data'):
    os.makedirs('data')
    os.makedirs('data/deputies')
    os.makedirs('data/transcripts')

if __name__ == '__main__':
    download_transcripts()
    download_deputies()
