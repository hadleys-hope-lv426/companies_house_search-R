# 🕵️ Companies House Search-R  

A Python-based open-source intelligence (OSINT) script for gathering and exporting UK Companies House data about company officers and entities.

## 🚀 Features  

- Search by officer name, company name, or company number
- Retrieves all appointments, including resigned and dissolved companies
- Outputs results to both CSV and JSON
- Combines all results into a single file for easier analysis
- Includes officer IDs for traceability

## 🧩 Installation  

Before you start, you will need a Companies House API key which you can get for free from Companies House.

You will need to visit: https://developer.company-information.service.gov.uk/get-started, sign up for an account and follow the instructions to generate an API key.  

🧾 Create a virtual environment

💻 Linux / macOS

	python3 -m venv myenv
	source myenv/bin/activate
	
🪟 Windows (PowerShell)

	python -m venv myenv
	myenv\Scripts\activate

	To deactivate at any time: deactivate

⚙️ Clone the repository:
   
   	git clone https://github.com/hadleys-hope-lv426/companies_house_search-R.git
   	cd companies_house_search-R
   	pip install requests

   	Add your Companies House API key to the config.json file

🕹️ Usage
	
	Search by Officer: python3 companies_house_search-R.py --officer "Jane Doe"
	Search by Company Name: python3 companies_house_search-R.py --company "BBC"
	Search by Company Number: python3 companies_house_search-R.py --number "112233445"

⚠️ Disclaimer

This tool is intended for lawful OSINT and research purposes only.
DO NOT use this tool to violate the Companies House Terms of Use.



