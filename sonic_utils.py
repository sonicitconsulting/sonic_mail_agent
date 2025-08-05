import logging
import sys
import os
import yaml
import time
import zipfile
from datetime import datetime, timedelta
import shutil
import uuid
import json
import inspect
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()
LOGLEVEL = os.getenv('LOGLEVEL')

def start_logger():
    '''
    Inizializza il logger di sistema
    '''
    log_level = LOGLEVEL
    if log_level == 'info':
        logger = logging.INFO
    if log_level == 'debug':
        logger = logging.DEBUG

    logging.basicConfig(
        level=logger,  # Set the desired log level
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)  # Print logs to console
        ]
    )


def write_log_message(log_message, loglevel='info'):
    '''
    Scrive un messaggio sul log di sistema
    :param log_message: messaggio da scrivere
    :param loglevel: livello di logging (info, warning, error, critical
    '''
    if loglevel == 'debug':
        logging.debug(log_message)
    if loglevel == 'info':
        logging.info(log_message)
    if loglevel == 'warning':
        logging.warning(log_message)
    if loglevel == "error":
        logging.error(log_message)
    if loglevel == "critical":
        logging.critical(log_message)



def wait_cycle():

    wait_time = int(os.getenv('WAIT_CYCLE'))
    write_log_message("Entering wait cycle for " + str(wait_time) + " seconds")

    time.sleep(wait_time)


def sleep_system():
    '''
    Mette in sleep il sistema per 24 ore
    :return:
    '''

    write_log_message("Entering sleep mode for servicing", 'warning')
    time.sleep(24 * 60 * 60)


def remove_files_by_extension(folder, extension):
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith('.json'):
                os.remove(os.path.join(root, file))


def unzip_file(zip_path, extract_to_path, delete_zip=True):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to_path)
    # Remove the zip file after extraction
    if delete_zip:
        os.remove(zip_path)


def delete_file(file_path):
    '''
    Cancella un file
    :param file_path: percorso completo file da cancellare
    :return:
    '''

    os.unlink(file_path)


def convert_timestamp(ts):
    return datetime.fromtimestamp(float(ts)).strftime('%Y-%m-%d %H:%M:%S')


def get_ordered_file_list(folder):
    files_with_dates = [(file, os.path.getmtime(os.path.join(folder, file))) for file in os.listdir(folder)]

    # Ordinare i file in base alla data di modifica
    sorted_files_with_dates = sorted(files_with_dates, key=lambda x: x[1])

    # Estrarre solo i nomi dei file ordinati
    sorted_files = [file for file, date in sorted_files_with_dates]

    return sorted_files


def clear_folder(folder):
    """
    Cancella tutto il contenuto della folder specificata.

    :param folder: Il percorso della folder da svuotare.
    """
    # Verifica se la folder esiste
    if os.path.exists(folder):
        # Itera su tutti gli elementi nella folder
        for elemento in os.listdir(folder):
            percorso_elemento = os.path.join(folder, elemento)
            try:
                # Se l'elemento è un file, lo elimina
                if os.path.isfile(percorso_elemento) or os.path.islink(percorso_elemento):
                    os.unlink(percorso_elemento)
                # Se l'elemento è una directory, la elimina ricorsivamente
                elif os.path.isdir(percorso_elemento):
                    shutil.rmtree(percorso_elemento)
            except Exception as e:
                write_log_message(f"Errore durante l'eliminazione di {percorso_elemento}: {e}", 'error')
    else:
        write_log_message(f"La folder {folder} non esiste.", 'error')


def get_current_timestamp():
    # Ottieni l'ora corrente come oggetto datetime
    current_time = datetime.now()
    # Formatta l'oggetto datetime come stringa nel formato MariaDB
    formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
    return formatted_time


def initialize_log_file():

    LOG_FOLDER = 'log'

    filename = os.path.join(LOG_FOLDER, get_current_timestamp()+"_find_similar_log.csv")

    line = 'Prog.,Timestamp,Doc. Id,File Name,Stored on,Libro/Cartella,Note'

    write_line_to_file(filename, line)

    return filename


def write_line_to_file(filename, line_to_add):

    line_to_add += "\n"

    with open(filename, 'a') as file:
        file.write(line_to_add)


def generate_random_filename(extension='.jpg', folder=None):
    '''
    Genera un filename univoco basato su uuid
    :param extension: estensione del file (.jpg default)
    '''
    # Generate a random UUID (Universally Unique Identifier)
    random_uuid = str(uuid.uuid4())

    # Remove dashes from the UUID to create a valid filename
    filename = random_uuid.replace("-", "")
    filename += extension

    if folder is not None:
        filename = os.path.join(folder, filename)

    return filename


def complete_filters(filters_str):
    # Valori di default
    default_filters = {"isValidated": False, "duplications": False}

    if not filters_str:
        # Se filters_str è None o vuoto, ritorna direttamente i valori di default
        return default_filters

    try:
        # Prova a convertire filters_str in un dizionario
        filters = json.loads(filters_str)
    except (json.JSONDecodeError, TypeError):
        # Se il parsing fallisce, ritorna i valori di default
        return default_filters

    # Controlla e completa eventuali valori mancanti
    for key, value in default_filters.items():
        if key not in filters:
            filters[key] = value

    return filters

def create_or_replace_folder(folder_name):
    """
    Crea una cartella con il nome specificato. Se la cartella esiste già,
    la cancella e la ricrea.

    :param folder_name: Nome della cartella da creare
    """
    # Controlla se la cartella esiste
    if os.path.exists(folder_name):
        # Cancella la cartella e il suo contenuto
        shutil.rmtree(folder_name)
        print(f"La cartella '{folder_name}' è stata cancellata.")

    # Crea la cartella
    os.makedirs(folder_name)

def clear_folder_2(folder):

    shutil.rmtree(folder)

def get_caller():
    return inspect.stack()[1].function


def check_time_interval(timestamp_1, timestamp_2, interval):

    start_time = datetime.strptime(timestamp_1, '%Y-%m-%d %H:%M:%S')
    end_time = datetime.strptime(timestamp_2, '%Y-%m-%d %H:%M:%S')

    time_ago = end_time - timedelta(interval)

    if start_time < time_ago:
        return False
    else:
        return True

def html_to_text(html_content):
    """Estrae testo puro dal contenuto HTML"""
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(separator="\n", strip=True)





