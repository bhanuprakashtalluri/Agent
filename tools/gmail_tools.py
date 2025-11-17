"""Utilities for interacting with Gmail through the Google API."""

import base64
import os
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from langchain.tools import tool

from .llm_cache import cached_tool


# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 
          'https://www.googleapis.com/auth/gmail.send']

CREDENTIALS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'gmail_credentials.json')
TOKEN_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'gmail_token.json')


def get_gmail_service():
    """Authenticate with Gmail and return the service plus an optional error."""
    print("\n[get_gmail_service] Called")
    creds = None
    
    # Load existing token
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    
    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_PATH):
                return None, "Gmail credentials file not found. Please set up OAuth2 credentials."
            
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    
    service = build('gmail', 'v1', credentials=creds)
    return service, None


@tool
@cached_tool(ttl_seconds=60 * 60, cache_type="gmail_profile", write_to_query_store=True)
def get_my_email() -> str:
    """
    Get the authenticated user's own email address.
    Use this when the user says 'send to myself' or 'my email'.
    
    Returns:
        The user's email address
    """
    print("\n[get_my_email] Called")
    try:
        service, error = get_gmail_service()
        if error:
            print(f"[get_my_email] Error: {error}")
            return f"Error: {error}"
        profile = service.users().getProfile(userId='me').execute()
        email = profile.get('emailAddress', 'Unknown')
        print(f"[get_my_email] Output: {email}")
        return f"Your email address is: {email}"
    except Exception as e:
        print(f"[get_my_email] Exception: {str(e)}")
        return f"Error getting email address: {str(e)}"


@tool
@cached_tool(ttl_seconds=60 * 5, cache_type="gmail_search", write_to_query_store=True)
def search_gmail(query: str, max_results: int = 10) -> str:
    """Search Gmail messages using the native query syntax.

    Args:
        query: Gmail-compatible search expression.
        max_results: Maximum messages to retrieve.

    Returns:
        Summary of matches with basic metadata and snippets.
    """
    print(f"\n[search_gmail] Input: query={query}, max_results={max_results}")
    try:
        service, error = get_gmail_service()
        if error:
            return f"Error: {error}"
        
        # Search messages
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return f"No emails found matching: {query}"
        
        output = [f"Found {len(messages)} emails:\n"]
        
        for msg in messages:
            # Get message details
            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            
            headers = message['payload']['headers']
            from_header = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
            
            snippet = message.get('snippet', '')
            
            output.append(f"\n---\nFrom: {from_header}\nSubject: {subject}\nDate: {date}\nSnippet: {snippet}\n")
        
        return "\n".join(output)
    
    except Exception as e:
        return f"Error searching Gmail: {str(e)}"


@tool
@cached_tool(ttl_seconds=60 * 5, cache_type="gmail_read", write_to_query_store=True)
def read_gmail(email_id: str) -> str:
    """Return the full content of a Gmail message identified by *email_id*.

    Args:
        email_id: Identifier obtained via :func:`search_gmail`.

    Returns:
        Plain-text representation of the message body with key headers.
    """
    try:
        service, error = get_gmail_service()
        if error:
            return f"Error: {error}"
        
        message = service.users().messages().get(
            userId='me',
            id=email_id,
            format='full'
        ).execute()
        
        headers = message['payload']['headers']
        from_header = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
        
        # Get email body
        parts = message['payload'].get('parts', [])
        body = ''
        
        if parts:
            for part in parts:
                if part['mimeType'] == 'text/plain':
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
        else:
            # Message has no parts, body is directly in payload
            if 'data' in message['payload']['body']:
                body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')
        
        return f"""From: {from_header}
Subject: {subject}
Date: {date}

{body}"""
    
    except Exception as e:
        return f"Error reading email: {str(e)}"


@tool
def send_gmail(to: str, subject: str, body: str) -> str:
    """Send an email via Gmail after validating the required fields.

    Args:
        to: Recipient email address supplied by the user.
        subject: Subject line to use for the outgoing message.
        body: Plain-text email body.

    Returns:
        Success confirmation or a descriptive error string.
    """
    try:
        # Validate inputs
        if not to or '@' not in to:
            return "Error: Invalid email address. Please provide a valid recipient email address."
        
        # Check for placeholder emails
        placeholder_domains = ['example.com', 'test.com', 'dummy.com', 'placeholder.com']
        if any(domain in to.lower() for domain in placeholder_domains):
            return f"Error: '{to}' appears to be a placeholder email. Please provide the actual recipient's email address."
        
        if not subject or subject.strip() == '':
            return "Error: Email subject is required. Please provide a clear subject line."
        
        if not body or body.strip() == '':
            return "Error: Email body is required. Please provide the email content."
        
        service, error = get_gmail_service()
        if error:
            return f"Error: {error}"
        
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        send_message = service.users().messages().send(
            userId='me',
            body={'raw': raw}
        ).execute()
        
        return f"✓ Email sent successfully!\nTo: {to}\nSubject: {subject}\nMessage ID: {send_message['id']}"
    
    except Exception as e:
        return f"Error sending email: {str(e)}"
