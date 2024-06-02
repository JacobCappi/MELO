import os.path
import base64
import json
import re
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
import requests

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def main():
  """Shows basic usage of the Gmail API.
  Lists the user's Gmail labels.
  """
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
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    # Call the Gmail API
    service = build("gmail", "v1", credentials=creds)
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q="is:unread").execute()
    
    # Returns Id's of messages that are unread
    messages = results.get('messages',[]);

    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()                
        email_data = msg['payload']['headers']
        sender = [values['value'] for values in email_data if values['name'] == 'From']
        print('--------------------------------')
        print(sender)

        # Need to wait a bit to collect some of these purchase emails.... 
        # Don't know what to parse yet.
        try:
          for p in msg['payload']['parts']:
              if p['mimeType'] in ['text/plain']:
                  data = base64.urlsafe_b64decode(p['body']['data']).decode('utf-8')
                  print(data)
        except BaseException as error:
          # for some reason, sometimes, parts is not used ~_~
          payload = msg['payload']['body']
          if p['mimeType'] in ['text/plain']:
              data = base64.urlsafe_b64decode(p['body']['data']).decode('utf-8')
              print(data)
          print(base64.urlsafe_b64decode(payload['data']).decode('utf-8'))
          pass

  except HttpError as error:
    # TODO(developer) - Handle errors from gmail API.
    print(f"An error occurred: {error}")


if __name__ == "__main__":
  main()
