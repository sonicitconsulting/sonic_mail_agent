from dotenv import load_dotenv
import sonic_utils as utils
from sonic_o365_library import MailReader
import sonic_mago_library as mago

utils.start_logger()
utils.write_log_message("Starting Mail Agent Service")
load_dotenv()


if __name__ == "__main__":

    while True:

        mail_reader = MailReader()

        if not mail_reader.get_access_token():
            utils.write_log_message("Impossibile ottenere il token di accesso. Uscita.")
            print()
            break

        emails = mail_reader.get_unread_emails()

        for mail in emails:
            email_id = mail["id"]
            utils.write_log_message(f"Email id: {email_id}")
            old_subject = mail.get("subject", None)
            mail_sender = mail['from']['emailAddress']['address']
            mail_body = utils.html_to_text(mail['body']['content'])

            has_ref_id = mago.check_reference_id(old_subject)

            if not has_ref_id:
                #bearer_token = mago.atium_login()
                bearer_token = True
                if bearer_token:

                    #is_valid_client, atium_client_id = mago.atium_check_user(mail_sender, bearer_token)
                    is_valid_client, atium_client_id = True, 12345
                    if is_valid_client:
                        #return_code = mago.open_ticket(atium_client_id, bearer_token, service_area='Undistinguished',
                        #                               description=mail_body)
                        return_code = True
                        if return_code:
                            utils.write_log_message("Ticket aperto con successo")
                            new_subject = f"Ticket Opened - {old_subject}"
                            res = mail_reader.update_email_subject(email_id, new_subject)

                            mail_reader.mark_email_as_read(email_id)

                        else:
                            utils.write_log_message("Apertura ticket non riuscita", "error")

        utils.wait_cycle()