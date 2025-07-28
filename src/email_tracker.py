import imaplib
import email
from email.header import decode_header
import pandas as pd
from datetime import datetime, timedelta
import re
import logging
import os

class EmailResponseTracker:
    def __init__(self, config):
        self.config = config
        self.email_config = config['email_config']
        self.excel_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data',
            config['excel_file']
        )
        self.logger = logging.getLogger(__name__)
    
    def connect_to_email(self):
        """Connect to email server"""
        try:
            if self.email_config['email'] == 'your_email@gmail.com':
                self.logger.warning("Email not configured")
                return None
                
            mail = imaplib.IMAP4_SSL(
                self.email_config['imap_server'], 
                self.email_config['imap_port']
            )
            mail.login(self.email_config['email'], self.email_config['password'])
            self.logger.info("Successfully connected to email server")
            return mail
        except Exception as e:
            self.logger.error(f"Error connecting to email: {e}")
            return None
    
    def extract_company_from_email(self, email_content, sender):
        """Extract company name from email content or sender"""
        try:
            # Try to extract from sender domain
            if '@' in sender:
                domain = sender.split('@')[1].lower()
                # Remove common email suffixes and get company name
                company_domain = domain.split('.')[0]
                
                # Skip common email providers
                skip_domains = ['gmail', 'yahoo', 'outlook', 'hotmail', 'aol', 'icloud']
                if company_domain not in skip_domains:
                    return company_domain.replace('-', ' ').title()
            
            # Try to extract from email signature or content
            signature_patterns = [
                r'Best regards,\s*\n.*?\n(.*?)(?:\n|$)',
                r'Sincerely,\s*\n.*?\n(.*?)(?:\n|$)',
                r'Thanks,\s*\n.*?\n(.*?)(?:\n|$)',
                r'(\w+\s+\w+)\s*\|\s*(.+?)(?:\n|$)',
                r'From:\s*(.+?)(?:\n|$)'
            ]
            
            for pattern in signature_patterns:
                matches = re.findall(pattern, email_content, re.IGNORECASE | re.MULTILINE)
                if matches:
                    for match in matches:
                        if isinstance(match, tuple):
                            company = match[1] if len(match) > 1 else match[0]
                        else:
                            company = match
                        
                        company = company.strip()
                        if len(company.split()) <= 3 and len(company) > 2:
                            return company
            
            return "Unknown Company"
            
        except Exception as e:
            self.logger.warning(f"Error extracting company from email: {e}")
            return "Unknown Company"
    
    def categorize_response(self, subject, content):
        """Categorize the type of response"""
        try:
            subject_lower = subject.lower()
            content_lower = content.lower()
            
            # Rejection keywords
            rejection_keywords = [
                'unfortunately', 'regret', 'not moving forward', 'not selected',
                'decided to go', 'other candidates', 'not the right fit',
                'will not be', 'have chosen', 'do not meet', 'unsuccessful'
            ]
            
            # Interview keywords  
            interview_keywords = [
                'interview', 'schedule', 'next step', 'phone call', 'meet',
                'discussion', 'chat', 'available', 'calendar', 'zoom',
                'teams meeting', 'would like to speak', 'set up a time'
            ]
            
            # Interest keywords
            interest_keywords = [
                'interested', 'review your', 'impressive', 'experience',
                'background', 'skills', 'qualified', 'would like to learn more',
                'tell us more', 'additional information'
            ]
            
            # Auto-reply keywords
            auto_reply_keywords = [
                'out of office', 'automatic reply', 'currently away',
                'will respond', 'received your email'
            ]
            
            if any(keyword in content_lower for keyword in auto_reply_keywords):
                return 'Auto-Reply'
            elif any(keyword in content_lower for keyword in rejection_keywords):
                return 'Rejection'
            elif any(keyword in content_lower for keyword in interview_keywords):
                return 'Interview Request'
            elif any(keyword in content_lower for keyword in interest_keywords):
                return 'Interested'
            else:
                return 'Other'
                
        except Exception as e:
            self.logger.warning(f"Error categorizing response: {e}")
            return 'Other'
    
    def check_for_responses(self, days_back=7):
        """Check for recruiter responses in email"""
        mail = self.connect_to_email()
        if not mail:
            return []
        
        responses = []
        
        try:
            mail.select('inbox')
            
            # Search for emails from the last few days
            since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
            status, message_ids = mail.search(None, f'SINCE {since_date}')
            
            if status == 'OK' and message_ids[0]:
                message_ids = message_ids[0].split()
                self.logger.info(f"Found {len(message_ids)} emails to check")
                
                # Check last 100 emails maximum
                for msg_id in message_ids[-100:]:
                    try:
                        status, msg_data = mail.fetch(msg_id, '(RFC822)')
                        email_body = msg_data[0][1]
                        email_message = email.message_from_bytes(email_body)
                        
                        # Extract email details
                        subject = decode_header(email_message["Subject"])[0][0]
                        if isinstance(subject, bytes):
                            subject = subject.decode()
                        
                        sender = email_message.get("From")
                        date_received = email_message.get("Date")
                        
                        # Get email content
                        content = self.extract_email_content(email_message)
                        
                        # Check if this might be a job-related response
                        if self.is_job_related(subject, content, sender):
                            company = self.extract_company_from_email(content, sender)
                            response_type = self.categorize_response(subject, content)
                            
                            response = {
                                'sender': sender,
                                'subject': subject,
                                'content': content[:1000],  # First 1000 chars
                                'date_received': date_received,
                                'company': company,
                                'response_type': response_type
                            }
                            responses.append(response)
                    
                    except Exception as e:
                        self.logger.warning(f"Error processing email {msg_id}: {e}")
                        continue
            
            mail.close()
            mail.logout()
            self.logger.info(f"Found {len(responses)} job-related emails")
            
        except Exception as e:
            self.logger.error(f"Error checking emails: {e}")
        
        return responses
    
    def extract_email_content(self, email_message):
        """Extract text content from email"""
        content = ""
        
        try:
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        try:
                            payload = part.get_payload(decode=True)
                            if payload:
                                content += payload.decode('utf-8', errors='ignore')
                        except Exception as e:
                            self.logger.warning(f"Error decoding email part: {e}")
            else:
                try:
                    payload = email_message.get_payload(decode=True)
                    if payload:
                        content = payload.decode('utf-8', errors='ignore')
                except Exception as e:
                    self.logger.warning(f"Error decoding email: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error extracting email content: {e}")
        
        return content
    
    def is_job_related(self, subject, content, sender):
        """Determine if email is job application related"""
        try:
            job_keywords = [
                'application', 'position', 'role', 'interview', 'resume',
                'cv', 'candidate', 'hiring', 'recruitment', 'job',
                'opportunity', 'thank you for applying', 'your interest'
            ]
            
            text_to_check = (subject + ' ' + content + ' ' + sender).lower()
            
            # Count job-related keywords
            keyword_count = sum(keyword in text_to_check for keyword in job_keywords)
            
            # Skip obvious spam/automated emails unless they have strong job indicators
            spam_indicators = ['unsubscribe', 'marketing', 'promotion', 'deal', 'sale']
            if any(indicator in text_to_check for indicator in spam_indicators):
                return keyword_count >= 3
            
            # Skip automated system emails unless job-related
            automated_senders = ['noreply', 'no-reply', 'donotreply', 'automated']
            if any(auto in sender.lower() for auto in automated_senders):
                return keyword_count >= 2
            
            return keyword_count >= 1
            
        except Exception as e:
            self.logger.warning(f"Error checking if email is job-related: {e}")
            return False
    
    def match_responses_to_applications(self, responses):
        """Match email responses to job applications in Excel"""
        try:
            if not os.path.exists(self.excel_file):
                self.logger.warning(f"Excel file not found: {self.excel_file}")
                return 0
                
            df = pd.read_excel(self.excel_file)
            applied_jobs = df[df['Status'] == 'Applied'].copy()
            
            if applied_jobs.empty:
                self.logger.info("No applied jobs found to match responses")
                return 0
            
            matches_made = 0
            
            for response in responses:
                best_match = None
                best_score = 0
                
                for idx, job in applied_jobs.iterrows():
                    score = 0
                    company_name = str(job['Company']).lower()
                    response_company = response['company'].lower()
                    
                    # Company name matching (highest priority)
                    if company_name in response_company or response_company in company_name:
                        score += 5
                    
                    # Check if company name appears in sender domain
                    if '@' in response['sender']:
                        domain = response['sender'].split('@')[1].lower()
                        company_clean = company_name.replace(' ', '').replace('-', '')
                        if company_clean in domain.replace('-', '').replace('.', ''):
                            score += 3
                    
                    # Job title matching
                    job_title = str(job['Title']).lower()
                    title_words = job_title.split()
                    subject_lower = response['subject'].lower()
                    
                    for word in title_words:
                        if len(word) > 3 and word in subject_lower:
                            score += 1
                    
                    # Date proximity (applied recently = more likely to get response)
                    if pd.notna(job['Date_Applied']):
                        try:
                            applied_date = pd.to_datetime(job['Date_Applied'])
                            days_since_applied = (datetime.now() - applied_date).days
                            if days_since_applied <= 7:
                                score += 2
                            elif days_since_applied <= 14:
                                score += 1
                        except:
                            pass
                    
                    if score > best_score:
                        best_score = score
                        best_match = idx
                
                # Update the Excel file if we found a good match
                if best_match is not None and best_score >= 3:
                    # Check if response is already recorded
                    if pd.isna(df.loc[best_match, 'Recruiter_Response']) or df.loc[best_match, 'Recruiter_Response'] == '':
                        df.loc[best_match, 'Recruiter_Response'] = response['response_type']
                        df.loc[best_match, 'Response_Date'] = datetime.now().strftime('%Y-%m-%d')
                        
                        # Create detailed notes
                        notes = f"From: {response['sender']}\n"
                        notes += f"Subject: {response['subject']}\n"
                        notes += f"Type: {response['response_type']}\n"
                        notes += f"Content Preview: {response['content'][:300]}..."
                        
                        df.loc[best_match, 'Notes'] = notes
                        matches_made += 1
                        
                        self.logger.info(f"Matched response to: {df.loc[best_match, 'Title']} at {df.loc[best_match, 'Company']}")
            
            # Save updated Excel file
            if matches_made > 0:
                df.to_excel(self.excel_file, index=False)
                self.logger.info(f"Updated Excel file with {matches_made} recruiter responses")
            
            return matches_made
            
        except Exception as e:
            self.logger.error(f"Error matching responses to applications: {e}")
            return 0
    
    def check_and_update_responses(self):
        """Main method to check for responses and update Excel"""
        try:
            responses = self.check_for_responses()
            if responses:
                matches = self.match_responses_to_applications(responses)
                return matches
            return 0
        except Exception as e:
            self.logger.error(f"Error in check_and_update_responses: {e}")
            return 0
