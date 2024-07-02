import yaml
import logging
import imaplib
import pandas as pd
import json
import email

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

def get_emails_to_delete(mail, filepath):
    with open(filepath, 'r') as file:
        data = json.load(file)
        emails_to_delete = data['emails']

    outdir = "C:\\Users\\jonny\\Downloads"
    summary = pd.DataFrame(columns=['Email', 'Count'])
    for e in emails_to_delete:
        _, messages = mail.search(None, '(FROM "{}")'.format(e))
        print(messages)
        for num in messages[0].split():
            header = mail.fetch(num, "(UID BODY[HEADER])")[1]
            resp, text = mail.fetch(num, "(UID BODY[TEXT])")[1]
            resp = str(resp)
            ml = email.message_from_string(resp)
            print(ml.get_content_maintype())
            for part in ml.walk():
                print(part.get_filename())
                if part.get_content_maintype() != 'multipart' and part.get('Content-Disposition') is not None:
                    open(outputdir + '/' + part.get_filename(), 'wb').write(part.get_payload(decode=True))
            mail.store(num, '+FLAGS', '\\Seen') # Email flags can be: Seen, Answered, Flagged, Deleted, Draft, Recent
            summary = summary._append({'Email': e, 'Count': len(num)}, ignore_index=True)
    return summary

#test comment for push
def main():
    credentials = load_credentials('credentials.yaml')
    mail = connect_to_gmail_imap(*credentials)
    summary = get_emails_to_delete(mail, 'emails.json')
    print(summary)
    
if __name__ == "__main__":
    main()