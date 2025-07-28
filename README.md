markdown# 
Job Application Tracker Agent

An automated system that helps you track job applications by scraping job portals, managing applications in Excel, and monitoring recruiter responses via email.

## 🚀 Features

- **Automated Job Scraping**: Daily searches on Indeed and LinkedIn
- **Excel Management**: Structured tracking of all job applications
- **Status Monitoring**: Tracks when you change status to "Applied"
- **Email Response Detection**: Automatically detects and categorizes recruiter responses
- **Scheduled Execution**: Runs daily at your specified time
- **Smart Matching**: Matches email responses to specific job applications

## 📋 Quick Start

### 1. Download and Setup
```bash
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
bash./scripts/run.sh --run-once
4. Start Daily Automation
bash./scripts/run.sh --schedule
📊 Excel File Structure
ColumnDescriptionDate_FoundWhen job was discoveredTitleJob titleCompanyCompany nameLocationJob locationWebsite_LinkDirect link to job postingPortalSource (Indeed, LinkedIn)StatusFound/Applied/Interview/RejectedDate_AppliedWhen you appliedRecruiter_ResponseType of response receivedResponse_DateWhen response was receivedNotesAdditional information
🔄 Workflow

Daily Search: System finds new jobs matching your criteria
Excel Update: New jobs added with status "Found"
Manual Application: You change status to "Applied" when you apply
Response Tracking: System monitors email for recruiter responses
Auto-Matching: Responses matched to specific applications
Notifications: Daily summary sent to your email

⚙️ Configuration
Job Search Parameters
json{
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


Use this password in config file

🛠️ Commands
bash# Run once for testing
./scripts/run.sh --run-once

# Start daily scheduler
./scripts/run.sh --schedule

# Windows users
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
├── backups/              # Excel file backups
├── scripts/              # Setup and run scripts
└── requirements.txt      # Python dependencies
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
🔒 Security

Never commit credentials to version control
Use environment variables for sensitive data
Regular backups of your job application data
Monitor for IP blocking from job portals

📈 Advanced Features

Custom Filters: Add salary, company size filters
Multiple Portals: Easy to add new job sites
Notification Options: Slack, Discord integration
Analytics: Track application success rates
Resume Matching: AI-powered job matching

🆘 Support

Check logs in logs/ directory
Review configuration in config/job_config.json
Test individual components separately
Ensure all dependencies are installed

📜 License
This project is open source. Use responsibly and respect job portal terms of service.
⚠️ Disclaimer

Respect robots.txt and terms of service
Some job portals may limit automated access
Always review and customize applications manually
This tool assists but doesn't replace human judgment


---

## File: .gitignore
Virtual environment
venv/
env/
Data files
data/.xlsx
data/.csv
Log files
logs/*.log
Backup files
backups/
Python cache
pycache/
*.pyc
*.pyo
*.pyd
IDE files
.vscode/
.idea/
*.swp
*.swo
OS files
.DS_Store
Thumbs.db
Configuration with sensitive data
config/job_config_personal.json
Temporary files
*.tmp
*.temp

---

## File: LICENSE
MIT License
Copyright (c) 2024 Job Tracker Agent
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
