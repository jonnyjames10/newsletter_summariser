import yaml
import logging
import imaplib
import pandas as pd
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib, ssl
from email.message import Message
from bs4 import BeautifulSoup
from itertools import chain
from openai import OpenAI
from time import time

prompt = '''
    Please summarize the key learnings from the top 10 articles across these 5 newsletters. 
    For each article, provide the author, title, what newsletter the article was from, and a brief summary 
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
    _, selected_mails = mail.search(None, 'OR (FROM "mark@mathison.ai") (FROM "markmallard29@gmail.com")')

    print(len(selected_mails[0].split()))
    for num in selected_mails[0].split()[:3]: # Add index here (e.g., [:10]) to limit the number of emails received
        _, data = mail.fetch(num, '(RFC822)')
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

def send_email(body, from_email, to_email):
    try:
        with open('credentials.yaml', 'r') as file:
            credentials = yaml.safe_load(file)
            password = credentials['password']
    except Exception as e:
        logging.error("Failed to load credentials: {}".format(e))
        raise

    message = MIMEMultipart("alternative")
    message["Subject"] = "Your Daily AI News"
    message["From"] = from_email
    message["To"] = to_email

    text = body

    html = '<html>\n<body>\n<h1 style="text-align: center">Here is your AI news for the day</h1>'
    for line in body.split('\n'):
        if line[:3] == '###': break
        html += f'<p>{line}</p>\n'
    html += '</body>\n</html>'

    find = html.find('**')
    i = 1
    while find != -1:
        if i % 2 == 1:
            html = html[:find]+"<b>"+html[find + len('**'):]
        else:
            html = html[:find]+"</b>"+html[find + len('**'):]
        find = html.find('**', find + len('**') + 1)
        i += 1

    print(html)

    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
    message.attach(part2)

    # Create secure connection with server and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(from_email, password)
        server.sendmail(
            from_email, to_email, message.as_string()
        )

def access_api():
    with open('credentials.yaml', 'r') as file:
        credentials = yaml.safe_load(file)
        organisation = credentials['organisation']
        api_key = credentials['api_key']

    content = ""
    body = ''

    for i in ['5', '7']:
        with open(f'article_{i}.txt', 'r') as file:
            content = file.read()
    
        client = OpenAI(
            organization=organisation,
            #project='newsletter_summarizer',
            api_key=api_key
        )

        response = client.chat.completions.create(
            model = "gpt-3.5-turbo",
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": content}
            ]
        )

        body += response.choices[0].message.content
    
    response = client.chat.completions.create(
        model = "gpt-3.5-turbo",
        messages = [
            {"role": "system", "content": '''Summarise these stories into the 5 biggest and most important stories. For each article, 
             provide the author, title (with the link to the article embedded into this), date the article was written, what newsletter the artcile was from, and a brief summary of the 
             key learnings. The summary should include context around the issue, the methodology used, and the solution outlined.'''},
            {"role": "user", "content": body}
        ]
    )

    result = response.choices[0].message.content

    file_name = 'result.txt'
    f = open(file_name, "x")
    f.write(result)
    f.close()

    return result

def main():
    credentials = load_credentials('credentials.yaml')
    mail = connect_to_gmail_imap(*credentials)
    get_emails(mail, 'emails.json')
    body = access_api()
    send_email(body, 'jonnysj8@gmail.com', 'jonny.streatfeild-james@pax2pay.com')

if __name__ == "__main__":
    main()

#TODO: Make more efficient calls to the OpenAI API
#TODO: Look into webscraping rather than pulling emails from inbox. Create list of websites user gets most of their info from, pull main story on the home page for each website link