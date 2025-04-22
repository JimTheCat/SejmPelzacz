import datetime
import os

import requests

path = "data/transcripts/"


def __check_pdf_exists(term, num, date):
    """
    Sprawdza, czy plik PDF istnieje dla danego kadencji, numeru posiedzenia i daty.
    """
    pdf_path = f'{path}{term}/{num}/{date}.pdf'
    return os.path.exists(pdf_path)


def __check_date_compatibility(date):
    """
    Sprawdza, czy podana data jest zgodna z formatem oraz nie przekracza dzisiejszej daty.
    """
    try:
        date_to_compare = datetime.datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        print(f"Nieprawidłowy format daty: {date}")
        return False
    return date_to_compare <= datetime.date.today()


def download_transcripts():
    """
    Główna funkcja wykonująca przetwarzanie danych z API Sejmu.
    """
    # Pobieranie wszystkich kadencji z API Sejmu
    response = requests.get('https://api.sejm.gov.pl/sejm/term')
    terms = response.json()

    for term in terms:
        term_number = term['num']
        term_from = term['from']
        term_current = term['current']
        # Ustalamy datę zakończenia kadencji
        term_to = 'present'
        if not term_current:
            term_to = term['to']
        print(f'Przetwarzanie kadencji: {term_number} ({term_from} - {term_to})')

        # Tworzenie katalogu dla danej kadencji
        term_dir = f'{path}{term_number}'
        if not os.path.exists(term_dir):
            os.makedirs(term_dir)

        # Pobieranie posiedzeń dla danej kadencji
        response = requests.get(f'https://api.sejm.gov.pl/sejm/term{term_number}/proceedings')
        proceedings = response.json()

        for proceeding in proceedings:
            proceeding_num = proceeding['number']
            proceeding_dates = proceeding['dates']
            print(f'Przetwarzanie posiedzenia: {proceeding_num} ({proceeding_dates})')

            # Tworzenie katalogu dla danego posiedzenia
            proceeding_dir = f'{term_dir}/{proceeding_num}'
            if not os.path.exists(proceeding_dir):
                os.makedirs(proceeding_dir)
            # Przetwarzanie dat dla danego posiedzenia
            for date in proceeding_dates:
                print(f'Przetwarzanie daty: {date}')
                # Pominięcie przetwarzania, jeśli plik PDF już istnieje
                if __check_pdf_exists(term_number, proceeding_num, date):
                    print(f'Plik PDF dla {date} już istnieje')
                    continue
                # Sprawdzenie poprawności daty
                if not __check_date_compatibility(date):
                    print(f'Data {date} nie jest zgodna z kadencją {term_number}')
                    continue

                # Pobieranie transkryptu PDF
                response = requests.get(
                    f'https://api.sejm.gov.pl/sejm/term{term_number}/proceedings/{proceeding_num}/{date}/transcripts/pdf'
                )
                if response.status_code == 200:
                    pdf_path = f'{proceeding_dir}/{date}.pdf'
                    with open(pdf_path, 'wb') as f:
                        f.write(response.content)
                    print(f'Zapisano PDF: {pdf_path}')
                else:
                    print(f'Brak PDF dla {date}')
