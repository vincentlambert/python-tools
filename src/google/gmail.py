#
# Don't forgot to : source ./venv/bin/activate
# (to create venv :  python3 -m venv venv)
#
import os
import argparse
import httplib2

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

# try:
#     import argparse
#     flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
# except ImportError:
#     print('Import Error')
#     flags = None

PARSER = argparse.ArgumentParser(parents=[tools.argparser])
PARSER.add_argument('--list_labels', help='List labels', action='store_true')
PARSER.add_argument('--list_messages', help='List messages', action='store_true')
PARSER.add_argument('--labels_filter', help='List label Ids to filter')
PARSER.add_argument('--print_message_metadata', help='Print message meta data with specified Id')
PARSER.add_argument('--check_doubled_labeled', help='Check double labeled messages', action='store_true')
PARSER.add_argument('--clean_doubled_labeled', help='Clean double labeled messages', action='store_true')
PARSER.add_argument('--dry_run', help='Dry run', action='store_true')
PARSER.add_argument('--burst_mode', help='Burst mode', action='store_true')
ARGS = PARSER.parse_args()

SCOPES = 'https://mail.google.com/'
CLIENT_SECRET_FILE = '.google/client_id.json'
APPLICATION_NAME = 'Google API'

LOG_FILE = None

def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.google_credentials')

    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)

    credential_path = os.path.join(credential_dir, 'gmail-python-quickstart.json')
    store = Storage(credential_path)
    credentials = store.get()

    if not credentials or credentials.invalid:
        # flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow = client.flow_from_clientsecrets(os.path.join(home_dir, CLIENT_SECRET_FILE), SCOPES)
        flow.user_agent = APPLICATION_NAME

        credentials = tools.run_flow(flow, store, ARGS)

        print('Storing credentials to ' + credential_path)

    return credentials


def get_service(credentials):
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)

    return service


def list_labels(service):
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    if not labels:
        print('No labels found.')
    else:
      print('Labels:')
      for label in labels:
        print('Label [%-20s] %s' % (label['id'], label['name']))


def list_messages(service, labels_filter=None):
    results = service.users().messages().list(userId='me', labelIds=labels_filter).execute()
    messages = []

    # if not results:
    #     print('No messages found.')
    # else:
    #     messages.extend(results['messages'])
    #     # for message in messages:
    #     #     print(message)

    if 'messages' in results:
        messages.extend(results['messages'])

    while 'nextPageToken' in results:
        page_token = results['nextPageToken']
        results = service.users().messages().list(userId='me', labelIds=labels_filter, pageToken=page_token).execute()
        messages.extend(results['messages'])

    return messages


def print_message_metadata(service, message_id):
    message = service.users().messages().get(userId='me', id=message_id).execute()
    print('Message ID [%s]' % message_id)
    print('Message labels' + str(message['labelIds']))
    print('Message snippet: %s' % message['snippet'])
    print('---')

def get_message_labels(service, message_id):
    message = service.users().messages().get(userId='me', id=message_id).execute()
    return message['labelIds']


def has_custom_label(service, message_id):
    message = service.users().messages().get(userId='me', id=message_id).execute()
    for label_id in message['labelIds']:
        if label_id.startswith('Label_'):
            return True
    return False


def search_doubled_labeled(service):
    unfiltered_messages = list_messages(service, 'INBOX')
    filtered_messages = [message for message in unfiltered_messages if has_custom_label(service, message['id'])]
    return filtered_messages


def remove_inbox_label(service, message_id):
    service.users().messages().modify(userId='me', id=message_id, body={'removeLabelIds':['INBOX']}).execute()


def burst_search_and_clean_doubled_labeled(service):
    results = service.users().messages().list(userId='me', labelIds='INBOX').execute()

    if 'messages' in results:
        messages = []
        messages.extend(results['messages'])
        for message in messages:
            if(has_custom_label(service, message['id'])):
                print_message_metadata(service, message['id'])
                if not ARGS.dry_run:
                    remove_inbox_label(service, message['id'])

    while 'nextPageToken' in results:
        messages = []
        page_token = results['nextPageToken']
        results = service.users().messages().list(userId='me', labelIds='INBOX', pageToken=page_token).execute()
        messages.extend(results['messages'])
        for message in messages:
            if(has_custom_label(service, message['id'])):
                print_message_metadata(service, message['id'])
                if not ARGS.dry_run:
                    remove_inbox_label(service, message['id'])
                if LOG_FILE is not None:
                    LOG_FILE.write(message['id'] + '\n')
                    LOG_FILE.flush()


if __name__ == '__main__':
    LOG_FILE = open('moved_email.log', 'a')

    credentials = get_credentials()
    service = get_service(credentials)

    print('Running Gmail classifier')

    if ARGS.dry_run:
        print('***** Dry run mode *****')

    if ARGS.list_labels:
        list_labels(service)

    elif ARGS.list_messages:
        messages = list_messages(service, ARGS.labels_filter)
        for message in messages:
            print(message)

    elif ARGS.print_message_metadata:
        print_message_metadata(service, ARGS.get_message_metadata)

    elif ARGS.check_doubled_labeled:
        messages = search_doubled_labeled(service)
        for message in messages:
            print_message_metadata(service, message['id'])

    elif ARGS.clean_doubled_labeled:
        if not ARGS.burst_mode:
            messages = search_doubled_labeled(service)
            print('%s message(s) selected' % len(messages))
            print('---')
            for message in messages:
                print_message_metadata(service, message['id'])
                if not ARGS.dry_run:
                    remove_inbox_label(service, message['id'])
        else:
            print('running burst mode')
            print('---')
            burst_search_and_clean_doubled_labeled(service)

    if LOG_FILE is not None:
        LOG_FILE.close()
    print('Done')
