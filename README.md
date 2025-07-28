# 📂 Job Application Tracker Agent

An automated system that helps you track job applications by scraping job portals, managing applications in Excel, and monitoring recruiter responses via email.

---

## 🚀 Features

- **Automated Job Scraping**: Daily searches on Indeed and LinkedIn  
- **Excel Management**: Structured tracking of all job applications  
- **Status Monitoring**: Tracks when you change status to `Applied`  
- **Email Response Detection**: Automatically detects and categorizes recruiter responses  
- **Scheduled Execution**: Runs daily at your specified time  
- **Smart Matching**: Matches email responses to specific job applications  

---

## 📋 Quick Start

### 1. Download and Setup

# Clone or download the project
cd job_tracker_agent

# Run setup script
chmod +x scripts/deploy.sh
./scripts/deploy.sh
2. Configure Settings
Edit config/job_config.json:

Add your job search keywords
Set your preferred location
Configure email credentials (Gmail recommended)
3. Test Run
./scripts/run.sh --run-once
4. Start Daily Automation
./scripts/run.sh --schedule
📊 Excel File Structure

Column	Description
Date_Found	When job was discovered
Title	Job title
Company	Company name
Location	Job location
Website_Link	Direct link to job posting
Portal	Source (Indeed, LinkedIn)
Status	Found/Applied/Interview/Rejected
Date_Applied	When you applied
Recruiter_Response	Type of response received
Response_Date	When response was received
Notes	Additional information
🔄 Workflow

Daily Search: System finds new jobs matching your criteria
Excel Update: New jobs added with status "Found"
Manual Application: You change status to "Applied" when you apply
Response Tracking: System monitors email for recruiter responses
Auto-Matching: Responses matched to specific applications
Notifications: Daily summary sent to your email
⚙️ Configuration

Job Search Parameters
{
  "search_parameters": {
    "keywords": ["python developer", "software engineer"],
    "location": "Remote",
    "experience_level": ["entry", "mid"],
    "exclude_keywords": ["senior", "lead"]
  }
}
Email Setup (Gmail)
Enable 2-factor authentication
Generate App Password:
Google Account → Security → 2-Step Verification → App passwords
Generate password for "Mail"
Use this password in the config file.
🛠️ Commands

# Run once for testing
./scripts/run.sh --run-once

# Start daily scheduler
./scripts/run.sh --schedule
:: Windows users
run.bat --run-once
run.bat --schedule
📁 Project Structure

job_tracker_agent/
├── src/                    # Source code
│   ├── job_tracker.py     # Main application
│   ├── email_tracker.py   # Email response tracking
│   └── utils.py           # Utility functions
├── config/                # Configuration files
│   └── job_config.json    # Main configuration
├── data/                  # Excel files and data
├── logs/                  # Application logs
├── backups/               # Excel file backups
├── scripts/               # Setup and run scripts
└── requirements.txt       # Python dependencies
🔧 Troubleshooting

Common Issues
ChromeDriver not found

The system automatically downloads ChromeDriver
Ensure Chrome browser is installed
Email authentication failed

Use App Password, not regular password
Verify 2FA is enabled in Gmail
Check IMAP is enabled
No jobs found

Check your keywords in config
Verify portals are enabled
Some sites may temporarily block automated access
Excel file locked

Close Excel before running the script
Check file permissions in data/ folder
Debug Mode

Set logging level to DEBUG in the code for detailed logs.
