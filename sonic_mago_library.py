import re
import os
import requests
import sonic_utils as utils
from datetime import datetime

def check_reference_id(mail_subject: str) -> bool:

    #pattern = r"Rif\. \d{6}"
    pattern = r"Ticket opened"

    return re.search(pattern, mail_subject) is not None

def atium_login(timeout: int | float = 30) -> None:
    """
    Login su sistema Atium.
    Parameters"""

    atium_endpoint = os.getenv("ATIUM_ENDPOINT")
    atium_user = os.getenv("ATIUM_USER")
    atium_password = os.getenv("ATIUM_PASSWORD")
    if not all((atium_endpoint, atium_user, atium_password)):
        raise EnvironmentError(
            "Imposta le variabili ATIUM_ENDPOINT, ATIUM_USER e ATIUM_PASSWORD."
        )
    url = f"{atium_endpoint}/auth/login"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {"username": atium_user, "password": atium_password, "grant_type": "password"}

    response = requests.post(url, headers=headers, json=payload, timeout=timeout)

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()  # solleva se status >= 400
    except requests.RequestException as err:
        # Log dettagliato per debug
        utils.write_log_message("=== ERRORE HTTP ===", 'critical')
        if isinstance(err, requests.HTTPError):
            utils.write_log_message(f"=== STATUS === {response.status_code}")
            utils.write_log_message(f"=== HEADERS === {response.headers}")
            utils.write_log_message(f"=== BODY ===  {response.text}")
        return False

    # A questo punto lo status è 2xx: parse del JSON

    try:
        data = response.json()
    except ValueError:  # JSON decode error
        utils.write_log_message(f"Risposta non in formato JSON valido: {response.text}")
        return False

    auth_token = data.get("auth_token")
    if auth_token:
        return auth_token

    # Nessun token presente: considera la risposta non valida
    utils.write_log_message(f"JSON di risposta privo di 'auth_token': {data}")
    return False


def atium_check_user(customer_id: str, auth_bearer: str, timeout: int | float = 30) -> str:
    """Verifica se l'utente è registrato su Atium."""

    atium_endpoint = os.getenv("ATIUM_ENDPOINT")
    if not atium_endpoint:
        raise EnvironmentError("Imposta la variabile ATIUM_ENDPOINT.")

    url = f"{atium_endpoint}/modules/crm/checkCustomerExistance"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {auth_bearer}",
    }

    payload = {"searchString": customer_id}

    response = requests.post(url, headers=headers, json=payload, timeout=timeout)

    match response.status_code:
        case 200:
            data = response.json()
            user_id = data.get("CustSupp")
            return True, user_id
        case 204:
            return False, "Utente non registrato"
        case _:
            return False, f"Errore {response.status_code}: {response.text}"


def open_ticket(atium_user_id: str, auth_bearer: str, service_area: str, description: str,
                timeout: int | float = 30) -> bool:

    atium_endpoint = os.getenv("ATIUM_ENDPOINT")
    if not atium_endpoint:
        raise EnvironmentError("Imposta la variabile ATIUM_ENDPOINT.")

    url = f"{atium_endpoint}/modules/rapportino/createTicketFromExternal"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {auth_bearer}",
    }

    if service_area == 'Mago':
        template_id = 59
    else:
        template_id = 62

    payload = {"activityDate": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
               "activityTime": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
               "activityState": "AP",
               "customer": atium_user_id,
               "IsTicket": True,
               "templateId": template_id,
               "OpenedBy": 37,
               "description": description
               }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()  # solleva se status >= 400
    except requests.RequestException as err:
        # Log dettagliato per debug
        utils.write_log_message(f"=== ERRORE HTTP === {err}")
        if isinstance(err, requests.HTTPError):
            print(f"=== STATUS === {response.status_code}")
            print(f"=== HEADERS === {response.headers}")
            print(f"=== BODY ===  {response.text}")
        return False

    if response.status_code == 200:
        return True