import msal
import requests
from datetime import datetime
import os
import sonic_utils as utils


class MailReader:

    def __init__(self):

        CLIENT_ID = os.getenv('OFFICE_CLIENT_ID')
        CLIENT_SECRET = os.getenv('OFFICE_CLIENT_SECRET')
        TENANT_ID = os.getenv('OFFICE_TENANT_ID')
        self.USER_EMAIL = os.getenv('USER_EMAIL')


        self.authority = f"https://login.microsoftonline.com/{TENANT_ID}"
        self.scope = ["https://graph.microsoft.com/.default"]
        self.app = msal.ConfidentialClientApplication(
            client_id=CLIENT_ID,
            client_credential=CLIENT_SECRET,
            authority=self.authority
        )
        self.access_token = None

    def get_access_token(self):
        """Ottiene un token di accesso utilizzando il client credentials flow"""
        try:
            result = self.app.acquire_token_silent(self.scope, account=None)

            if not result:
                result = self.app.acquire_token_for_client(scopes=self.scope)

            if "access_token" in result:
                self.access_token = result["access_token"]
                return True
            else:
                utils.write_log_message(f"❌ Errore nell'acquisizione del token: {result.get('error_description', result)}", 'error')
                return False

        except Exception as e:

            utils.write_log_message(f"❌ Errore durante l'autenticazione: {e}", 'error')
            return False

    def get_unread_emails(self):
        """Legge solo le email non lette dalla casella specificata"""
        if not self.access_token:
            utils.write_log_message("❌ Token di accesso non disponibile", 'error')
            return None

        # Endpoint per ottenere solo le email non lette
        endpoint = f"https://graph.microsoft.com/v1.0/users/{self.USER_EMAIL}/messages"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        # Parametri per filtrare solo le email non lette
        params = {
            "$filter": "isRead eq false",  # Solo email non lette
            "$select": "id,subject,from,receivedDateTime,body,isRead",
            "$orderby": "receivedDateTime desc",  # Più recenti per prime
            "$top": 50  # Massimo 50 email per richiesta
        }

        try:
            response = requests.get(endpoint, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()
                emails = data.get("value", [])
                return emails
            else:
                utils.write_log_message(f"❌ Errore nella lettura delle email: {response.status_code}", 'error')
                utils.write_log_message(f"   Dettagli: {response.text}", 'error')
                return None

        except Exception as e:
            utils.write_log_message(f"❌ Errore durante la richiesta: {e}", 'error')
            return None

    def update_email_subject(self, email_id, new_subject):
        """Modifica il subject della mail data"""
        if not self.access_token:
            utils.write_log_message("Token non presente.", 'error')
            return False

        endpoint = f"https://graph.microsoft.com/v1.0/users/{self.USER_EMAIL}/messages/{email_id}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        data = {"subject": new_subject}
        try:
            response = requests.patch(endpoint, headers=headers, json=data)
            return response.status_code == 200
        except Exception as e:
            utils.write_log_message(f"Errore PATCH: {e}", 'error')
            return False

    def mark_email_as_read(self, email_id):
        """Marca una email come letta (opzionale)"""
        if not self.access_token:
            return False

        endpoint = f"https://graph.microsoft.com/v1.0/users/{self.USER_EMAIL}/messages/{email_id}"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        data = {
            "isRead": True
        }

        try:
            response = requests.patch(endpoint, headers=headers, json=data)
            return response.status_code == 200
        except Exception as e:
            utils.write_log_message(f"❌ Errore nel marcare l'email come letta: {e}", 'error')
            return False

    def get_email_details(self, email_id):
        """Ottiene i dettagli completi di una email specifica"""
        if not self.access_token:
            return None

        endpoint = f"https://graph.microsoft.com/v1.0/users/{self.USER_EMAIL}/messages/{email_id}"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        params = {
            "$select": "id,subject,from,receivedDateTime,body,hasAttachments,attachments"
        }

        try:
            response = requests.get(endpoint, headers=headers, params=params)

            if response.status_code == 200:
                return response.json()
            else:
                utils.write_log_message(f"❌ Errore nel recupero dettagli email: {response.status_code}", 'error')
                return None

        except Exception as e:
            utils.write_log_message(f"❌ Errore durante il recupero dettagli: {e}", 'error')
            return None
