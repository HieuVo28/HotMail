import imaplib
import email
from bs4 import BeautifulSoup
import re
from datetime import datetime
from typing import List, Dict
from ..core.config import settings
from email.header import decode_header
import logging
import requests
import json
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class AuthError(Exception):
    def __init__(self, error_code: str, message: str, correlation_id: str = None):
        self.error_code = error_code
        self.message = message
        self.correlation_id = correlation_id
        super().__init__(self.message)

class EmailService:
    def __init__(self, email_address: str, password: str, client_id: str, refresh_token: str):
        self.email_address = email_address
        self.password = password
        self.client_id = client_id
        self.refresh_token = refresh_token
        self.access_token = None
        self.imap_host = settings.IMAP_HOST
        self.imap_port = settings.IMAP_PORT
        self.get_access_token()

    def get_access_token(self):
        data = {
            'client_id': self.client_id,
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
        }
        try:
            res = requests.post('https://login.live.com/oauth20_token.srf', data=data)
            if res.status_code == 200:
                response_data = res.json()
                self.access_token = response_data.get('access_token')
                self.refresh_token = response_data.get('refresh_token', self.refresh_token)
                logger.info('Successfully obtained new access token')
            else:
                error_data = res.json()
                error_code = error_data.get('error', 'unknown_error')
                error_msg = error_data.get('error_description', 'Unknown error occurred')
                correlation_id = error_data.get('correlation_id')
                
                if error_code == 'invalid_grant':
                    raise AuthError(
                        error_code=error_code,
                        message="Token hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại để lấy refresh token mới.",
                        correlation_id=correlation_id
                    )
                else:
                    raise AuthError(
                        error_code=error_code,
                        message=error_msg,
                        correlation_id=correlation_id
                    )
        except requests.exceptions.RequestException as e:
            raise AuthError(
                error_code="request_failed",
                message=f"Không thể kết nối đến server xác thực: {str(e)}"
            )
        except json.JSONDecodeError:
            raise AuthError(
                error_code="invalid_response",
                message="Server trả về dữ liệu không hợp lệ"
            )

    def _generate_auth_string(self) -> str:
        if not self.access_token:
            self.get_access_token()
        return f"user={self.email_address}\1auth=Bearer {self.access_token}\1\1"

    def _decode_mime_words(self, text: str) -> str:
        decoded_words = decode_header(text)
        return ''.join([
            word.decode(encoding or 'utf-8') if isinstance(word, bytes) else word
            for word, encoding in decoded_words
        ])

    def _extract_text_from_email(self, msg) -> str:
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if content_type in ["text/plain", "text/html"] and "attachment" not in content_disposition:
                    payload = part.get_payload(decode=True)
                    if content_type == "text/html":
                        return BeautifulSoup(payload.decode('utf-8', errors='replace'), 'html.parser').get_text()
                    return payload.decode('utf-8', errors='replace')
        else:
            content_type = msg.get_content_type()
            payload = msg.get_payload(decode=True)
            if content_type == "text/html":
                return BeautifulSoup(payload.decode('utf-8', errors='replace'), 'html.parser').get_text()
            return payload.decode('utf-8', errors='replace')
        return ''

    async def get_otp_from_emails(self, folders: List[str] = None) -> List[Dict]:
        if folders is None:
            folders = ['INBOX', 'JUNK']
        
        try:
            client = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            auth_string = self._generate_auth_string()
            try:
                client.authenticate('XOAUTH2', lambda x: auth_string.encode())
            except imaplib.IMAP4.error as e:
                if 'AUTHENTICATE failed' in str(e):
                    logger.info('Auth failed, trying to refresh token')
                    self.get_access_token()
                    auth_string = self._generate_auth_string()
                    client.authenticate('XOAUTH2', lambda x: auth_string.encode())
                else:
                    raise AuthError(
                        error_code="imap_auth_failed",
                        message="Không thể xác thực với IMAP server"
                    )
            
            otp_list = []
            
            for folder in folders:
                client.select(folder)
                _, messages = client.search(None, 'ALL')
                email_ids = messages[0].split()
                latest_email_ids = email_ids[-5:] if len(email_ids) >= 5 else email_ids

                for email_id in latest_email_ids:
                    _, msg_data = client.fetch(email_id, '(RFC822)')
                    email_body = email.message_from_bytes(msg_data[0][1])
                    
                    subject = self._decode_mime_words(email_body.get("Subject", ""))
                    from_addr = self._decode_mime_words(email_body.get("From", ""))
                    date = email_body.get("Date")
                    
                    if re.search(r'Combo|Cabal|Mobile|verify', from_addr, re.IGNORECASE):
                        text = self._extract_text_from_email(email_body)
                        text = ' '.join(text.split())
                        
                        otp_match = re.search(r'\b\d{6}\b', text)
                        if otp_match:
                            try:
                                email_date = datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %z')
                                otp_list.append({
                                    'otp': otp_match.group(0),
                                    'date': email_date.isoformat(),
                                    'subject': subject,
                                    'from': from_addr
                                })
                            except ValueError as e:
                                logger.error(f"Error parsing date: {e}")

            client.logout()
            return sorted(otp_list, key=lambda x: x['date'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error in get_otp_from_emails: {e}")
            raise Exception(f"Failed to fetch emails: {str(e)}")

    async def search_emails(self, query: str, folders: List[str] = None) -> List[Dict]:
        if folders is None:
            folders = ['INBOX']
            
        try:
            client = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            auth_string = self._generate_auth_string()
            try:
                client.authenticate('XOAUTH2', lambda x: auth_string.encode())
            except:
                logger.info('Auth failed, trying to refresh token')
                self.get_access_token()
                auth_string = self._generate_auth_string()
                client.authenticate('XOAUTH2', lambda x: auth_string.encode())
            
            results = []
            
            for folder in folders:
                client.select(folder)
                search_criteria = f'SUBJECT "{query}" OR TEXT "{query}"'
                _, messages = client.search(None, search_criteria)
                
                for num in messages[0].split():
                    _, msg_data = client.fetch(num, '(RFC822)')
                    email_body = email.message_from_bytes(msg_data[0][1])
                    
                    subject = self._decode_mime_words(email_body.get("Subject", ""))
                    from_addr = self._decode_mime_words(email_body.get("From", ""))
                    date = email_body.get("Date")
                    
                    try:
                        email_date = datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %z')
                        results.append({
                            'subject': subject,
                            'from': from_addr,
                            'date': email_date.isoformat(),
                            'content': self._extract_text_from_email(email_body)[:500] + "..."
                        })
                    except ValueError as e:
                        logger.error(f"Error parsing date: {e}")
                        
            client.logout()
            return sorted(results, key=lambda x: x['date'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error in search_emails: {e}")
            raise Exception(f"Failed to search emails: {str(e)}") 