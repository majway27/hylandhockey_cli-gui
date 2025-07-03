"""
Gmail functionality for sending emails.
"""

import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from googleapiclient.discovery import build

from auth.google_auth import get_credentials
from config.config_manager import ConfigManager


def send_gmail(sender_email, to_email, subject, message_text, config_manager: ConfigManager = None):
    """
    Send an email using Gmail API.
    
    Args:
        sender_email (str): The email address of the sender
        to_email (str): The email address of the recipient
        subject (str): The subject of the email
        message_text (str): The HTML body text of the email
        config_manager (ConfigManager): Optional ConfigManager instance
        
    Returns:
        dict: The sent message object
    """
    creds = get_credentials(config_manager)
    service = build('gmail', 'v1', credentials=creds)

    # Create message
    message = MIMEMultipart('alternative')
    message['to'] = to_email
    message['from'] = sender_email
    message['subject'] = subject

    # Create plain text version by stripping HTML tags
    import re
    plain_text = re.sub('<[^<]+?>', '', message_text)
    text_part = MIMEText(plain_text, 'plain')
    html_part = MIMEText(message_text, 'html')
    message.attach(text_part)
    message.attach(html_part)

    # Encode the message
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    
    try:
        # Send the message
        message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        print(f'Message Id: {message["id"]}')
        return message
    except Exception as e:
        print(f'An error occurred: {e}')
        return None

def create_gmail_draft(sender_email, to_email, subject, message_text, config_manager: ConfigManager = None):
    """
    Create a draft email using Gmail API.
    
    Args:
        sender_email (str): The email address of the sender
        to_email (str): The email address of the recipient
        subject (str): The subject of the email
        message_text (str): The HTML body text of the email
        config_manager (ConfigManager): Optional ConfigManager instance
        
    Returns:
        dict: The created draft message object
    """
    creds = get_credentials(config_manager)
    service = build('gmail', 'v1', credentials=creds)

    # Create message
    message = MIMEMultipart('alternative')
    message['to'] = to_email
    message['from'] = sender_email
    message['subject'] = subject

    # Create plain text version by stripping HTML tags
    import re
    plain_text = re.sub('<[^<]+?>', '', message_text)
    text_part = MIMEText(plain_text, 'plain')
    html_part = MIMEText(message_text, 'html')
    message.attach(text_part)
    message.attach(html_part)

    # Encode the message
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    
    try:
        # Create the draft
        draft = service.users().drafts().create(
            userId='me',
            body={'message': {'raw': raw_message}}
        ).execute()
        print(f'Draft Id: {draft["id"]}')
        return draft
    except Exception as e:
        print(f'An error occurred: {e}')
        return None

def send_all_drafts(config_manager: ConfigManager = None):
    """
    Send all draft messages that have a recipient specified in the To: header.
    
    Args:
        config_manager (ConfigManager): Optional ConfigManager instance
        
    Returns:
        list: A list of dictionaries containing the results of each send operation,
              including success status and message ID or error message
    """
    creds = get_credentials(config_manager)
    service = build('gmail', 'v1', credentials=creds)
    
    results = []
    
    try:
        # Get all drafts
        drafts = service.users().drafts().list(userId='me').execute()
        
        if not drafts.get('drafts'):
            print('No drafts found')
            return results
            
        for draft in drafts['drafts']:
            try:
                # Get the full draft message
                draft_message = service.users().drafts().get(
                    userId='me',
                    id=draft['id']
                ).execute()
                
                # Get the message headers
                headers = draft_message['message']['payload']['headers']
                to_header = next((h['value'] for h in headers if h['name'].lower() == 'to'), None)
                
                # Only send if there's a recipient
                if to_header:
                    try:
                        # Create a new message from the draft
                        message = MIMEMultipart('alternative')
                        message['to'] = to_header
                        message['from'] = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'me')
                        message['subject'] = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
                        
                        # Get the message body
                        body = ''
                        is_html = False
                        if 'parts' in draft_message['message']['payload']:
                            for part in draft_message['message']['payload']['parts']:
                                if part['mimeType'] == 'text/html':
                                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                                    is_html = True
                                    break
                                elif part['mimeType'] == 'text/plain':
                                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        elif 'body' in draft_message['message']['payload']:
                            body = base64.urlsafe_b64decode(draft_message['message']['payload']['body']['data']).decode('utf-8')
                        
                        if is_html:
                            # Create plain text version by stripping HTML tags
                            import re
                            plain_text = re.sub('<[^<]+?>', '', body)
                            text_part = MIMEText(plain_text, 'plain')
                            html_part = MIMEText(body, 'html')
                            message.attach(text_part)
                            message.attach(html_part)
                        else:
                            text_part = MIMEText(body, 'plain')
                            message.attach(text_part)
                        
                        # Encode the message
                        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
                        
                        # Send the message
                        sent_message = service.users().messages().send(
                            userId='me',
                            body={'raw': raw_message}
                        ).execute()
                        
                        results.append({
                            'success': True,
                            'message_id': sent_message['id'],
                            'draft_id': draft['id']
                        })
                        
                        # Delete the draft after successful send
                        service.users().drafts().delete(
                            userId='me',
                            id=draft['id']
                        ).execute()
                        
                    except Exception as e:
                        results.append({
                            'success': False,
                            'draft_id': draft['id'],
                            'error': str(e)
                        })
                else:
                    results.append({
                        'success': False,
                        'draft_id': draft['id'],
                        'error': 'No recipient specified'
                    })
            except Exception as e:
                results.append({
                    'success': False,
                    'draft_id': draft['id'],
                    'error': f'Error processing draft: {str(e)}'
                })
                
        return results
        
    except Exception as e:
        print(f'An error occurred while processing drafts: {e}')
        return results 