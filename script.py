import yaml
import logging
import imaplib
import pandas as pd
import email
from bs4 import BeautifulSoup
from itertools import chain
from openai import OpenAI

prompt = '''
    Please summarize the key learnings from the top 10 articles across these 5 newsletters. 
    For each article, provide the author, title, date the article was written, and a brief summary 
    of the key learnings. The summary should include context around the issue, the methodology used, 
    and the solution outlined. Additionally, include a link to access the full article. Here are 
    the 5 newsletters:
'''

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
    _, selected_mails = mail.search(None, 'OR (FROM "noreply@medium.com") (FROM "markmallard29@gmail.com")')

    print(len(selected_mails[0].split()))
    for num in selected_mails[0].split()[:3]: # Add index here (e.g., [:10]) to limit the number of emails received
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
                decoded_message = message.decode()
                print("Message: \n", decoded_message)
                print("==========================================\n")
                file_name = f'article_{int(num)}.txt'
                f = open(file_name, "x")
                f.write(decoded_message)
                f.close()
                break
    return

def access_api():
    client = OpenAI(
        organization='org-RCHvmqk9Mhdjk5WOht6gFsyu',
        project='newsletter_summarizer',
    )

    return

#2nd test comment for push
def main():
    credentials = load_credentials('credentials.yaml')
    mail = connect_to_gmail_imap(*credentials)
    get_emails(mail, 'emails.json')

if __name__ == "__main__":
    main()

#TODO:
#   Extract headers, text and links from the emails
#   Use ChatGPT to extract summaries of articles