import requests
from requests.auth import HTTPBasicAuth
import csv
import json
import argparse
import time
from datetime import datetime

import json

with open("config.json") as f:
    config = json.load(f)

API_KEY = config["API_KEY"]
BASE_URL = "https://api.company-information.service.gov.uk"

def search_officers(name):
    url = f"{BASE_URL}/search/officers?q={name}"
    response = requests.get(url, auth=HTTPBasicAuth(API_KEY, ''))
    response.raise_for_status()
    return response.json().get("items", [])

def get_officer_appointments(officer_id):
    url = f"{BASE_URL}/officers/{officer_id}/appointments"
    response = requests.get(url, auth=HTTPBasicAuth(API_KEY, ''))
    response.raise_for_status()
    return response.json().get("items", [])

def get_company_details(company_number):
    """Get detailed company information including registered office address"""
    try:
        url = f"{BASE_URL}/company/{company_number}"
        response = requests.get(url, auth=HTTPBasicAuth(API_KEY, ''))
        if response.status_code == 200:
            data = response.json()
            # Extract address information
            address = data.get('registered_office_address', {})
            return {
                "company_name": data.get("company_name", ""),
                "company_status": data.get("company_status", ""),
                "company_type": data.get("type", ""),
                "incorporation_date": data.get("date_of_creation", ""),
                "registered_address": format_address(address)
            }
    except Exception as e:
        print(f"    Error fetching company details for {company_number}: {e}")
    
    return {
        "company_name": "",
        "company_status": "",
        "company_type": "",
        "incorporation_date": "",
        "registered_address": ""
    }

def format_address(address_dict):
    """Format address dictionary into a readable string"""
    if not address_dict:
        return ""
    
    parts = []
    fields = ['address_line_1', 'address_line_2', 'locality', 'region', 'postal_code', 'country']
    
    for field in fields:
        if address_dict.get(field):
            parts.append(address_dict[field])
    
    return ", ".join(parts)

def search_companies(name):
    url = f"{BASE_URL}/search/companies?q={name}"
    response = requests.get(url, auth=HTTPBasicAuth(API_KEY, ''))
    response.raise_for_status()
    return response.json().get("items", [])

def get_company_officers(company_number):
    all_officers = []
    start_index = 0
    items_per_page = 100

    while True:
        url = f"{BASE_URL}/company/{company_number}/officers?start_index={start_index}&items_per_page={items_per_page}"
        response = requests.get(url, auth=HTTPBasicAuth(API_KEY, ''))
        response.raise_for_status()
        data = response.json()

        items = data.get("items", [])
        all_officers.extend(items)

        if len(items) < items_per_page:
            break
        start_index += items_per_page

    return all_officers

def save_results_to_files(results, filename_prefix):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"{filename_prefix}_{timestamp}.csv"
    json_filename = f"{filename_prefix}_{timestamp}.json"

    # JSON
    with open(json_filename, "w", encoding="utf-8") as jf:
        json.dump(results, jf, indent=4)

    # CSV
    with open(csv_filename, "w", newline='', encoding="utf-8") as cf:
        writer = csv.writer(cf)
        if filename_prefix == "officers":
            writer.writerow([
                "Officer Name", 
                "Officer ID", 
                "Company Name", 
                "Company Number", 
                "Company Status",
                "Company Type",
                "Incorporation Date",
                "Registered Office Address",
                "Officer Role",
                "Appointed On", 
                "Resigned On"
            ])
            for officer in results:
                for company in officer["appointments"]:
                    writer.writerow([
                        officer["officer_name"],
                        officer["officer_id"],
                        company["company_name"],
                        company["company_number"],
                        company.get("company_status", ""),
                        company.get("company_type", ""),
                        company.get("incorporation_date", ""),
                        company.get("registered_address", ""),
                        company.get("officer_role", ""),
                        company.get("appointed_on", ""),
                        company.get("resigned_on", "")
                    ])
        elif filename_prefix == "companies":
            writer.writerow([
                "Company Name", 
                "Company Number", 
                "Company Status",
                "Company Type",
                "Incorporation Date",
                "Registered Office Address",
                "Officer Name", 
                "Officer Role", 
                "Appointed On", 
                "Resigned On"
            ])
            for company in results:
                for officer in company["officers"]:
                    writer.writerow([
                        company["company_name"],
                        company["company_number"],
                        company.get("company_status", ""),
                        company.get("company_type", ""),
                        company.get("incorporation_date", ""),
                        company.get("registered_address", ""),
                        officer["name"],
                        officer.get("officer_role", ""),
                        officer.get("appointed_on", ""),
                        officer.get("resigned_on", "")
                    ])
    print(f"[+] Results saved to {csv_filename} and {json_filename}")

def main():
    parser = argparse.ArgumentParser(description="Companies House OSINT Tool")
    parser.add_argument("--officer", help="Search by officer name")
    parser.add_argument("--company", help="Search by company name")
    parser.add_argument("--number", help="Search by company number")
    args = parser.parse_args()

    if args.officer:
        name = args.officer.strip()
        print(f"[+] Searching officers for: {name}")
        officers = search_officers(name)
        print(f"[+] Found {len(officers)} officer variations.\n")

        officer_results = []
        for o in officers:
            
            officer_link = o["links"]["self"]
            officer_id = officer_link.split("/officers/")[1].split("/")[0]
            officer_name = o["title"]

            print(f"--- Retrieving appointments for {officer_name} ({officer_id}) ---")
            try:
                appointments = get_officer_appointments(officer_id)
                print(f"  Found {len(appointments)} appointments.")
                
                enhanced_appointments = []
                for i, appointment in enumerate(appointments):
                    print(f"    Fetching company details {i+1}/{len(appointments)}...")
                    company_number = appointment["appointed_to"]["company_number"]
                    company_details = get_company_details(company_number)
                    
                    enhanced_appointment = {
                        "company_name": appointment["appointed_to"]["company_name"],
                        "company_number": company_number,
                        "company_status": company_details["company_status"],
                        "company_type": company_details["company_type"],
                        "incorporation_date": company_details["incorporation_date"],
                        "registered_address": company_details["registered_address"],
                        "officer_role": appointment.get("officer_role", ""),
                        "appointed_on": appointment.get("appointed_on", ""),
                        "resigned_on": appointment.get("resigned_on", "")
                    }
                    enhanced_appointments.append(enhanced_appointment)
                    
                    time.sleep(0.2)

                print(f"  Enhanced {len(enhanced_appointments)} appointments with company details.\n")

                officer_results.append({
                    "officer_name": officer_name,
                    "officer_id": officer_id,
                    "appointments": enhanced_appointments
                })
            except Exception as e:
                print(f"  Error retrieving appointments for {officer_name}: {e}\n")
                continue

        if officer_results:
            save_results_to_files(officer_results, "officers")
        else:
            print("[-] No appointments found for any officers.")
        return

    elif args.company:
        company_name = args.company.strip()
        print(f"[+] Searching companies for: {company_name}")
        companies = search_companies(company_name)
        print(f"[+] Found {len(companies)} company matches.\n")

        company_results = []
        for c in companies:
            number = c["company_number"]
            name = c["title"]
            print(f"--- Retrieving officers (active + resigned) for {name} ({number}) ---")

            company_details = get_company_details(number)
            
            officers = get_company_officers(number)
            print(f"  Found {len(officers)} total officers (active + resigned).\n")

            company_results.append({
                "company_name": company_details["company_name"] or name,
                "company_number": number,
                "company_status": company_details["company_status"],
                "company_type": company_details["company_type"],
                "incorporation_date": company_details["incorporation_date"],
                "registered_address": company_details["registered_address"],
                "officers": [
                    {
                        "name": o["name"],
                        "officer_role": o.get("officer_role", ""),
                        "appointed_on": o.get("appointed_on", ""),
                        "resigned_on": o.get("resigned_on", "")
                    } for o in officers
                ]
            })
        save_results_to_files(company_results, "companies")
        return

    elif args.number:
        company_number = args.number.strip()
        print(f"[+] Retrieving officers (active + resigned) for company number: {company_number}")
        
        company_details = get_company_details(company_number)
        
        officers = get_company_officers(company_number)
        print(f"[+] Found {len(officers)} total officers.\n")

        company_results = [{
            "company_name": company_details["company_name"] or company_number,
            "company_number": company_number,
            "company_status": company_details["company_status"],
            "company_type": company_details["company_type"],
            "incorporation_date": company_details["incorporation_date"],
            "registered_address": company_details["registered_address"],
            "officers": [
                {
                    "name": o["name"],
                    "officer_role": o.get("officer_role", ""),
                    "appointed_on": o.get("appointed_on", ""),
                    "resigned_on": o.get("resigned_on", "")
                } for o in officers
            ]
        }]
        save_results_to_files(company_results, "companies")
        return

    else:
        name = input("Enter the director's full name: ").strip()
        if name:
            print(f"[+] Searching officers for: {name}")
            officers = search_officers(name)
            print(f"[+] Found {len(officers)} officer variations.\n")

            officer_results = []
            for o in officers:
                
                officer_link = o["links"]["self"]
                officer_id = officer_link.split("/officers/")[1].split("/")[0]
                officer_name = o["title"]

                print(f"--- Retrieving appointments for {officer_name} ({officer_id}) ---")
                try:
                    appointments = get_officer_appointments(officer_id)
                    print(f"  Found {len(appointments)} appointments.")
                    
                   
                    enhanced_appointments = []
                    for i, appointment in enumerate(appointments):
                        print(f"    Fetching company details {i+1}/{len(appointments)}...")
                        company_number = appointment["appointed_to"]["company_number"]
                        company_details = get_company_details(company_number)
                        
                        enhanced_appointment = {
                            "company_name": appointment["appointed_to"]["company_name"],
                            "company_number": company_number,
                            "company_status": company_details["company_status"],
                            "company_type": company_details["company_type"],
                            "incorporation_date": company_details["incorporation_date"],
                            "registered_address": company_details["registered_address"],
                            "officer_role": appointment.get("officer_role", ""),
                            "appointed_on": appointment.get("appointed_on", ""),
                            "resigned_on": appointment.get("resigned_on", "")
                        }
                        enhanced_appointments.append(enhanced_appointment)
                        
                    
                        time.sleep(0.2)

                    print(f"  Enhanced {len(enhanced_appointments)} appointments with company details.\n")

                    officer_results.append({
                        "officer_name": officer_name,
                        "officer_id": officer_id,
                        "appointments": enhanced_appointments
                    })
                except Exception as e:
                    print(f"  Error retrieving appointments for {officer_name}: {e}\n")
                    continue

            if officer_results:
                save_results_to_files(officer_results, "officers")
            else:
                print("[-] No appointments found for any officers.")

if __name__ == "__main__":
    main()
