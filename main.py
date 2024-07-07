import os.path
import base64
import json
import re
import time
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
import requests

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

chase_to_csv = []
citi_to_csv = []
discover_to_csv = []

totals = [0, 0, 0]

def parse(date_utc, sender, subject):
  if 'transaction' not in subject:
    return
  
  if '$' not in subject:
    return

  sender_name = sender[0].split()[0]
  money = [d[1:] for d in subject.split() if '$' in d]
  money = money[0]
  csv_line = f'{date_utc}, {sender_name}, {money}, {subject}\n'

  if 'Chase' in sender_name:
    chase_to_csv.append(csv_line)
    totals[0] += float(money)
  elif 'Citi' in sender_name:
    citi_to_csv.append(csv_line)
    totals[1] += float(money)
  elif 'Discover' in sender_name:
    discover_to_csv.append(csv_line)
    totals[2] += float(money)

def check_mail(year_str, month_str):

  chase_total = float(0)
  citi_total = float(0)
  discover_total = float(0)

  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES)
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    # Call the Gmail API
    service = build("gmail", "v1", credentials=creds)
    next_month = int(month_str)+1;
    query_str = f"after:{year_str}/{month_str}/1 before:{year_str}/{next_month}/1"
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q=query_str).execute()
    
    # Returns Id's of messages that are unread
    messages = results.get('messages',[]);

    if (len(messages) == check_mail.mail_count):
      return

    f = open(f'{year_str}_{month_str}.csv', 'w')
    check_mail.mail_count = len(messages)

    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()                

        email_data = msg['payload']['headers']
        sender = [values['value'] for values in email_data if values['name'] == 'From']
        date_utc = [values['value'] for values in email_data if values['name'] == 'Date']

        payload = msg['payload']

        try:
          p = payload['headers']
          for a in p:
            if a['name'] == 'Subject':
              parse(date_utc, sender, a['value'])

        except BaseException as e:
          for pay in payload['parts']:
            p = pay['headers']
            for a in p:
              if a['name'] == 'Subject':
                parse(date_utc, sender, a['value'])
    
    f.write(f'CHASE BANK : ${totals[0] : .2f}\n')
    for message in chase_to_csv:
      f.write(message)

    f.write(f'\nCITI BANK : ${totals[1] : .2f}\n')
    for message in citi_to_csv:
      f.write(message)

    f.write(f'\nDISCOVER BANK : ${totals[2] : .2f}\n')
    for message in discover_to_csv:
      f.write(message)
    
    f.write(f'\nTOTAL: ${sum(totals) : .2f}\n')

  except HttpError as error:
    # TODO(developer) - Handle errors from gmail API.
    print(f"An error occurred: {error}")


def main():
  server_mode = False
  year_str = input('Year (as 4 int): ')
  check_mail.mail_count = 0;

  # Server mode
  if 's' in year_str:
    server_mode = True

  if not server_mode:
    month_str = input('Month (as 2 int): ')
    check_mail(year_str, month_str)
    return
  
  while(True):
    c = datetime.now()

    year_str = c.year
    month_str = c.month
    check_mail(year_str, month_str)
    time.sleep(60)



if __name__ == "__main__":
  main()
