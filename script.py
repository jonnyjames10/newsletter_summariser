import yaml
import logging
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib, ssl
import os
from openai import OpenAI

prompt1 = '''
    You are a creating a newsletter of the the top AI news stories. Summarise the stories from this newsletter. The goal is to engage the reader into clicking a link to take the user to the article. Summarise 
    the stories into this format:
    - **Title:** [Title of the article]
    - **Author:** [Author of the article]
    - **Newsletter:** [Name of the newsletter the article was taken from]
    - **Summary:** [Summary of the article (more details about the summary below)]
    - **Link:** [A link which goes straight to the article's page on the website]
    Please ensure the summary is close to 500 characters and includes context around the issue, the methodology used, and the solution outlined. Also, don't include any feedback and just the articles. Here are the articles:
'''

prompt2 = '''
    Please summarize the key learnings from the top 5 articles across these newsletters into this format:
        - **Title:** [Title of the article]
        - **Author:** [Author of the article]
        - **Newsletter:** [Name of the newsletter the article was taken from]
        - **Summary:** [Summary of the article (more details about the summary below)]
        - **Link:** [A link which goes straight to the article's page on the website]
    Please ensure the summary is close to 500 characters and includes context around the issue, the methodology used, and the solution outlined. Also, don't include any feedback and just the articles. Here are the articles:
'''

new_prompt = '''
    You are a creating a newsletter of the 5 most important stories from newsletters. Go through the articles from each newsletter, and out of these summarise the top 5 of them. The goal is to engage the reader into
    clicking a link to take the user to the article. Summarise the article into this format:
    - **Title:** [Title of the article]
    - **Author:** [Author of the article]
    - **Newsletter:** [Name of the newsletter the article was taken from]
    - **Summary:** [Summary of the article (more details about the summary below)]
    - **Link:** [A link which goes straight to the article's page on the website]
    Please ensure the summary is close to 500 characters and includes context around the issue, the methodology used, and the solution outlined. Also, don't include any feedback and just the articles. Here are the articles:
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

def get_emails(mail):
    _, selected_mails = mail.search(None, 'UnSeen')

    print(len(selected_mails[0].split()))
    for num in selected_mails[0].split()[:4]: # Add index here (e.g., [:10]) to limit the number of emails received
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
    
    client = OpenAI(
        organization=organisation,
        #project='newsletter_summarizer',
        api_key=api_key
    )

    content = ""
    body = ''

    dir = os.fsencode('/home/jonny/Documents/repos/newsletter_summariser')
    for file in os.listdir(dir):
        filename = os.fsdecode(file)
        if filename.endswith(".txt") and filename.startswith("article"):

            print(filename)
            with open(filename, 'r') as file:
                content = file.read()

            response = client.chat.completions.create(
                model = "gpt-4-turbo",
                messages = [
                    {"role": "system", "content": prompt1},
                    {"role": "user", "content": content}
                ]
            )

            body += response.choices[0].message.content
    
    response = client.chat.completions.create(
        model = "gpt-4-turbo",
        messages = [
            {"role": "system", "content": new_prompt},
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
    get_emails(mail)
    body = access_api()
    send_email(body, 'jonnysj8@gmail.com', 'jonny.streatfeild-james@pax2pay.com')

if __name__ == "__main__":
    main()

#TODO: Make more efficient calls to the OpenAI API
#TODO: Look into webscraping rather than pulling emails from inbox. Create list of websites user gets most of their info from, pull main story on the home page for each website link