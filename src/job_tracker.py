import pandas as pd
import time
import schedule
from datetime import datetime
import json
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.email_tracker import EmailResponseTracker
from src.utils import setup_logging, create_directories

class JobTrackingAgent:
    def __init__(self, config_file='config/job_config.json'):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_path = os.path.join(self.project_root, config_file)

        # Setup logging
        log_dir = os.path.join(self.project_root, 'logs')
        setup_logging(log_dir)
        self.logger = logging.getLogger(__name__)
        # Create necessary directories
        create_directories(self.project_root)

        # setup from config
        self.config = self.load_config()
        self.excel_file = os.path.join(self.project_root, 'data', self.config.get('excel_file', 'job_applications.xlsx'))

        # Setup driver
        self.setup_driver()

        # Initialize email tracker
        self.email_tracker = EmailResponseTracker(self.config)

    def load_config(self):
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                self.logger.info("Configuration loaded successfully")
                return config
        except FileNotFoundError:
            self.logger.error(f"Configuration file not found: {self.config_path}")
            # Create default config
            default_config = self.create_default_config()
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            self.logger.info("Created default configuration file")
            return default_config

    def create_default_config(self):
        """Create default configuration"""
        return {
            "search_parameters": {
                "keywords": ["python developer", "software engineer", "data scientist"],
                "location": "Remote",
                "experience_level": ["entry", "mid"],
                "job_type": ["full-time", "contract"],
                "exclude_keywords": ["senior", "lead", "manager"]
            },
            "portals": {
                "indeed": {
                    "enabled": True,
                    "base_url": "https://indeed.com/jobs",
                    "selectors": {
                        "job_card": "[data-jk]",
                        "title": "h2 a span",
                        "company": "[data-testid='company-name']",
                        "link": "h2 a",
                        "location": "[data-testid='job-location']"
                    }
                },
                "linkedin": {
                    "enabled": True,
                    "base_url": "https://linkedin.com/jobs/search"
                }
            },
            "email_config": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "email": "your_email@gmail.com",
                "password": "your_app_password",
                "imap_server": "imap.gmail.com",
                "imap_port": 993
            },
            "excel_file": "job_applications.xlsx",
            "schedule_time": "09:00",
            "max_jobs_per_run": 20,
            "delay_between_requests": 2
        }

    def setup_driver(self):
        """Setup Selenium WebDriver with automatic ChromeDriver management"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

            # Use WebDriver Manager to automatically download and manage ChromeDriver or uses predownloaded one
            try:
                CHROMEDRIVER_PATH = "./src/chromedriver"
                service = Service(CHROMEDRIVER_PATH)
            except:
                print("Chromedriver not found in opt, defaulting to download")
                service = Service(ChromeDriverManager().install())

            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.logger.info("WebDriver setup successful")

        except Exception as e:
            self.logger.error(f"Error setting up WebDriver: {e}")
            raise

    def load_or_create_excel(self):
        """Load existing Excel file or create new one"""
        columns = [
            'Date_Found', 'Title', 'Company', 'Location', 'Website_Link',
            'Portal', 'Status', 'Date_Applied', 'Recruiter_Response',
            'Response_Date', 'Notes'
        ]

        try:
            if os.path.exists(self.excel_file):
                df = pd.read_excel(self.excel_file)
                # Add missing columns if they don't exist
                for col in columns:
                    if col not in df.columns:
                        df[col] = ''
                self.logger.info(f"Loaded existing Excel file with {len(df)} records")
            else:
                df = pd.DataFrame(columns=columns) #type: ignore
                self.logger.info("Created new Excel file structure")

            return df

        except Exception as e:
            self.logger.error(f"Error loading Excel file: {e}")
            return pd.DataFrame(columns=columns) #type: ignore

    def scrape_indeed(self, keywords: str, location: str) -> List[Dict]:
        """Scrape job listings from Indeed"""
        jobs = []
        try:
            search_url = f"https://indeed.com/jobs?q={keywords.replace(' ', '+')}&l={location.replace(' ', '+')}"
            self.logger.info(f"Scraping Indeed: {search_url}")

            self.driver.get(search_url)
            time.sleep(3)

            job_cards = self.driver.find_elements(By.CSS_SELECTOR, '[data-jk]')
            self.logger.info(f"Found {len(job_cards)} job cards on Indeed")

            for i, card in enumerate(job_cards[:self.config.get('max_jobs_per_run', 20)]):
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, 'h2 a span')
                    company_elem = card.find_element(By.CSS_SELECTOR, '[data-testid="company-name"]')
                    link_elem = card.find_element(By.CSS_SELECTOR, 'h2 a')
                    href = link_elem.get_attribute('href') or ''
                
                    job = {
                        'title': title_elem.text.strip(),
                        'company': company_elem.text.strip(),
                        'location': location,
                        'link': 'https://indeed.com' + href,
                        'portal': 'Indeed',
                        'date_found': datetime.now().strftime('%Y-%m-%d')
                    }
                    jobs.append(job)

                except Exception as e:
                    self.logger.warning(f"Error parsing Indeed job card {i}: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error scraping Indeed: {e}")

        return jobs

    def scrape_linkedin(self, keywords: str, location: str) -> List[Dict]:
        """Scrape job listings from LinkedIn"""
        jobs = []
        try:
            search_url = f"https://linkedin.com/jobs/search/?keywords={keywords.replace(' ', '%20')}&location={location.replace(' ', '%20')}"
            self.logger.info(f"Scraping LinkedIn: {search_url}")

            self.driver.get(search_url)
            time.sleep(5)

            self.scroll_till_bottom()

            job_cards = self.driver.find_elements(By.CSS_SELECTOR, '.job-search-card')
            self.logger.info(f"Found {len(job_cards)} job cards on LinkedIn")

            for i, card in enumerate(job_cards[:self.config.get('max_jobs_per_run', 20)]):
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, '.base-search-card__title')
                    company_elem = card.find_element(By.CSS_SELECTOR, '.base-search-card__subtitle')
                    link_elem = card.find_element(By.CSS_SELECTOR, '.base-card__full-link')

                    # so every card here is a live pointer to an element in DOM managed by selenium, some text will not be loaded on time when .text is called and therefore get_attribute must be called which ensures text is present when needed
                    job = {
                        'title': title_elem.text.strip() or title_elem.get_attribute('innerText').strip(),
                        'company': company_elem.text.strip() or company_elem.get_attribute('innerText').strip(),
                        'location': location,
                        'link': link_elem.get_attribute('href'),
                        'portal': 'LinkedIn',
                        'date_found': datetime.now().strftime('%Y-%m-%d')
                    }

                    jobs.append(job)

                except Exception as e:
                    self.logger.warning(f"Error parsing LinkedIn job card {i}: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error scraping LinkedIn: {e}")

        return jobs

    def filter_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Filter jobs based on parameters"""
        filtered_jobs = []
        search_params = self.config['search_parameters']
        exclude_keywords = search_params.get('exclude_keywords', [])

        for job in jobs:
            title_lower = job['title'].lower()

            # Check if title contains any exclude keywords
            if any(keyword.lower() in title_lower for keyword in exclude_keywords):
                print(f"{title_lower} excluded since it contains excluded keywords")
            else:
                filtered_jobs.append(job)
            # # Check if title contains desired keywords
            # if any(keyword.lower() in title_lower for keyword in search_params['keywords']):
            #     filtered_jobs.append(job)

        self.logger.info(f"Filtered {len(jobs)} jobs down to {len(filtered_jobs)}")
        return filtered_jobs

    def new_job_scraper_worker(self, keyword: str, search_params: Dict, portals: Dict) -> List[Dict]:

        jobs_by_worker = []
        self.logger.info(f"Searching for: {keyword}")
        # Scrape Indeed if enabled
        if portals.get('indeed', {}).get('enabled', True):
            indeed_jobs = self.scrape_indeed(keyword, search_params.get('location', 'Remote'))
            jobs_by_worker.extend(indeed_jobs)
            time.sleep(self.config.get('delay_between_requests', 2))

        # Scrape LinkedIn if enabled
        if portals.get('linkedin', {}).get('enabled', True):
            linkedin_jobs = self.scrape_linkedin(keyword, search_params.get('location', 'Remote'))
            jobs_by_worker.extend(linkedin_jobs)
            time.sleep(self.config.get('delay_between_requests', 2))

        return jobs_by_worker

    def check_for_new_jobs(self) -> List[Dict]:
        """Check all portals for new job listings"""
        all_jobs = []
        search_params = self.config['search_parameters']
        portals = self.config['portals']

        with ThreadPoolExecutor(max_workers=5) as executor:
            
            future_to_result = {executor.submit(self.new_job_scraper_worker, keyword, search_params, portals): (worker_id + 1,keyword) for worker_id,keyword in enumerate(search_params['keywords'])}
            for future in as_completed(future_to_result):
                worker_id,current_future = future_to_result[future]
                try:
                    jobs = future.result()
                    all_jobs.extend(jobs)
                    self.logger.info(f"Found {len(jobs)} jobs for keyword: {current_future} by worker {worker_id}")
                except Exception as e:
                    self.logger.error(f"Error in job scraping thread for keyword {current_future}: {e} (worker {worker_id})")

        self.logger.info(f"Total jobs found across all workers: {len(all_jobs)}")

        # Filter jobs
        filtered_jobs = self.filter_jobs(all_jobs)

        # Remove duplicates
        unique_jobs = []
        seen = set()
        for job in filtered_jobs:
            key = (job['title'], job['company'])
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)

        self.logger.info(f"Found {len(unique_jobs)} unique new jobs")
        return unique_jobs

    def update_excel_with_new_jobs(self, new_jobs: List[Dict]):
        """Add new jobs to Excel file"""
        df = self.load_or_create_excel()

        new_rows = []
        for job in new_jobs:
            # Check if job already exists
            existing = df[
                (df['Title'].str.lower() == job['title'].lower()) &
                (df['Company'].str.lower() == job['company'].lower())
            ]

            if existing.empty:
                new_row = {
                    'Date_Found': job['date_found'],
                    'Title': job['title'],
                    'Company': job['company'],
                    'Location': job['location'],
                    'Website_Link': job['link'],
                    'Portal': job['portal'],
                    'Status': 'Found',
                    'Date_Applied': '',
                    'Recruiter_Response': '',
                    'Response_Date': '',
                    'Notes': ''
                }
                new_rows.append(new_row)

        if new_rows:
            new_df = pd.DataFrame(new_rows)
            df = pd.concat([df, new_df], ignore_index=True)

            # Ensure data directory exists
            os.makedirs(os.path.dirname(self.excel_file), exist_ok=True)

            df.to_excel(self.excel_file, index=False)
            self.logger.info(f"Added {len(new_rows)} new jobs to {self.excel_file}")
        else:
            self.logger.info("No new jobs found")

    def check_recruiter_responses(self):
        """Check for recruiter responses using email tracker"""
        try:
            response_count = self.email_tracker.check_and_update_responses()
            self.logger.info(f"Checked recruiter responses, found {response_count} new responses")
        except Exception as e:
            self.logger.error(f"Error checking recruiter responses: {e}")

    def send_notification(self, message: str):
        """Send email notification"""
        try:
            email_config = self.config['email_config']

            if email_config['email'] == 'your_email@gmail.com':
                self.logger.warning("Email not configured, skipping notification")
                return

            msg = MIMEMultipart()
            msg['From'] = email_config['email']
            msg['To'] = email_config['email']
            msg['Subject'] = "Job Tracker Daily Update"

            msg.attach(MIMEText(message, 'plain'))

            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['email'], email_config['password'])
            text = msg.as_string()
            server.sendmail(email_config['email'], email_config['email'], text)
            server.quit()

            self.logger.info("Notification sent successfully")

        except Exception as e:
            self.logger.error(f"Error sending notification: {e}")

    def daily_job_check(self):
        """Main function to run daily job check"""
        self.logger.info("=" * 50)
        self.logger.info("Starting daily job check...")
        start_time = datetime.now()

        try:
            # Check for new jobs
            new_jobs = self.check_for_new_jobs()

            # Update Excel with new jobs
            self.update_excel_with_new_jobs(new_jobs)

            # Check for recruiter responses
            self.check_recruiter_responses()

            # Create summary message
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            message = f"""Job Tracker Daily Summary
                Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                Duration: {duration:.2f} seconds
                New Jobs Found: {len(new_jobs)}
                Excel File: {self.excel_file}

                Jobs by Portal:
                """

            portal_counts = {}
            for job in new_jobs:
                portal = job['portal']
                portal_counts[portal] = portal_counts.get(portal, 0) + 1

            for portal, count in portal_counts.items():
                message += f"- {portal}: {count} jobs\n"

            if not new_jobs:
                message += "No new jobs found today."

            self.logger.info(f"Daily job check completed. Found {len(new_jobs)} new jobs in {duration:.2f} seconds")

            # Send notification
            self.send_notification(message)

        except Exception as e:
            error_msg = f"Error in daily job check: {e}"
            self.logger.error(error_msg)
            self.send_notification(error_msg)

        finally:
            self.logger.info("=" * 50)

    def start_scheduler(self):
        """Start the daily scheduler"""
        schedule_time = self.config.get('schedule_time', '09:00')
        schedule.every().day.at(schedule_time).do(self.daily_job_check)

        self.logger.info(f"Job scheduler started. Will run daily at {schedule_time}")
        print(f"🚀 Job Tracker Agent started! Will run daily at {schedule_time}")
        print("Press Ctrl+C to stop")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            self.logger.info("Scheduler stopped by user")
            print("\n👋 Job Tracker Agent stopped")
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup resources"""
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
                self.logger.info("WebDriver closed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def scroll_till_bottom(self):
        """Scroll to bottom and click 'Show more' button when available"""

        scroll_wait_time = 2
        idle_scrolls = 0
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:
            # Scroll down slightly to trigger lazy UI behavior
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_wait_time)

            # Now try clicking the button (after scroll)
            try:
                show_more_btn = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.infinite-scroller__show-more-button'))
                )

                if show_more_btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", show_more_btn)
                    time.sleep(3)

            except Exception as e:
                print("No visible 'Show more jobs' button:", e)

            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                idle_scrolls += 1
                if idle_scrolls > 10:
                    print("No new content loaded after several scrolls. Stopping.")
                    break
            else:
                idle_scrolls = 0

            last_height = new_height


def main():
    """Main entry point"""
    try:

        agent = JobTrackingAgent()

        # Check command line arguments
        if len(sys.argv) > 1:
            if sys.argv[1] == '--run-once':
                print("🔍 Running job check once...")
                agent.daily_job_check()
                print("✅ Job check completed!")
            elif sys.argv[1] == '--schedule':
                agent.start_scheduler()
            else:
                print("Usage:")
                print("  python job_tracker.py --run-once   # Run once for testing")
                print("  python job_tracker.py --schedule   # Start daily scheduler")
        else:
            # Default behavior - run once
            print("🔍 Running job check once...")
            agent.daily_job_check()
            print("✅ Job check completed!")
            print("\nTo run daily automatically, use: python job_tracker.py --schedule")

    except KeyboardInterrupt:
        print("\n👋 Stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        logging.getLogger(__name__).error(f"Main error: {e}")
    finally:
        if 'agent' in locals():
            agent.cleanup()

if __name__ == "__main__":
    main()
