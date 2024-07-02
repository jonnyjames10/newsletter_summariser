import yaml
import logging
import imaplib
import pandas as pd
import json
import email
from bs4 import BeautifulSoup
from itertools import chain

def load_credentials(filepath):
    try:
        with open(filepath, 'r') as file:
            credentials = yaml.safe_load(file)
            user = credentials['user']
            password = credentials['password']
            return user, password
    except Exception as e:
        logging.error("Failed to load credentials: {}".format(e))
        raise

def connect_to_gmail_imap(user, password):
    imap_url = 'imap.gmail.com'
    try:
        mail = imaplib.IMAP4_SSL(imap_url)
        mail.login(user, password)
        mail.select('Notes')  # Connect to the inbox.
        return mail
    except Exception as e:
        logging.error("Connection failed: {}".format(e))
        raise

def get_emails(mail, filepath):
    with open(filepath, 'r') as file:
        data = json.load(file)
        emails_to_delete = data['emails']
    
    _, selected_mails = mail.search(None, 'OR (FROM "noreply@medium.com") (FROM "jonnysj8@gmail.com")')

    print(len(selected_mails[0].split()))
    for num in selected_mails[0].split()[1:3]: # Add index here (e.g., [1:3]) to limit the number of emails received
        _, data = mail.fetch(num , '(RFC822)')
        _, bytes_data = data[0]

        #convert the byte data to message
        email_message = email.message_from_bytes(bytes_data)
        print("\n===========================================")

        #access data
        print("Subject: ",email_message["subject"])
        print("To:", email_message["to"])
        print("From: ",email_message["from"])
        print("Date: ",email_message["date"])
        for part in email_message.walk():
            if part.get_content_type()=="text/plain" or part.get_content_type()=="text/html":
                message = part.get_payload(decode=True)
                print("Message: \n", message.decode())
                print("==========================================\n")
                break

    return

#2nd test comment for push
def main():
    criteria = {}
    uid_max = 0
    credentials = load_credentials('credentials.yaml')
    mail = connect_to_gmail_imap(*credentials)
    summary = get_emails(mail, 'emails.json')
    print(summary)
    
if __name__ == "__main__":
    main()