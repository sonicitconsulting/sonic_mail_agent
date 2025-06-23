from O365 import Account
import os
from dotenv import load_dotenv
import time
import sonic_utils as utils
import sonic_mago_library as mago

utils.start_logger()
utils.write_log_message("Starting Mail Agent Service"
                        "")
load_dotenv()
CLIENT_ID = os.getenv('OFFICE_CLIENT_ID')
CLIENT_SECRET = os.getenv('OFFICE_CLIENT_SECRET')
TENANT_ID = os.getenv('OFFICE_TENANT_ID')

WAIT_CYCLE = os.getenv('WAIT_CYCLE')

if __name__ == "__main__":

    while True:
        try:
            utils.write_log_message("Avvio autenticazione")

            # Autenticazione
            credentials = (CLIENT_ID, CLIENT_SECRET)
            account = Account(credentials, auth_flow_type='credentials', tenant_id=TENANT_ID)

            if not account.authenticate():
                utils.write_log_message("Autenticazione fallita")
                utils.sleep_system()
                continue

            utils.write_log_message("Autenticazione riuscita")

            # Accesso alla mailbox
            mailbox = account.mailbox()
            inbox = mailbox.inbox_folder()
            messages = inbox.get_messages(limit=5)  # Legge ultime 5 email

            if not messages:
                print("📭 Nessuna nuova mail trovata")
            else:
                utils.write_log_message(f"Trovate {len(messages)} email")

            # Elaborazione email
            for message in messages:
                utils.write_log_message(f"ID messaggio: {message.object_id}")
                utils.write_log_message(f"Oggetto originale: {message.subject}")

                has_ref_id = mago.check_reference_id(message.subject)

                if not has_ref_id:
                    bearer_token = mago.atium_login()
                    if bearer_token:
                        is_valid_client, atium_client_id = mago.atium_check_user(message.sender.address, bearer_token)
                        if is_valid_client:
                            return_code = mago.open_ticket(atium_client_id, bearer_token, service_area='Undistinguished', description=message.get_body_text())
                            if return_code:
                                utils.write_log_message("Ticket aperto con successo")
                                nuovo_oggetto = f"Ticket Opened - {message.subject}"
                                message.subject = nuovo_oggetto
                                message.save()
                            else:
                                utils.write_log_message("Apertura ticket non riuscita", "error")

            utils.write_log_message("\n⏳ Attesa prossimo controllo...")

        except Exception as e:
            utils.write_log_message(f"⚠️ Errore durante l'operazione: {str(e)}")

        # Attesa prima della prossima esecuzione
        time.sleep(WAIT_CYCLE)