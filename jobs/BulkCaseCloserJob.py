import sys
import os

# Add the parent directory (integration root) to sys.path to find vendored TIPCommon
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
import urllib3
from datetime import datetime, timedelta
import re
import time
from soar_sdk.SiemplifyJob import SiemplifyJob
from TIPCommon import extract_action_param

# Disable SSL warnings for lab environment if needed
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

INTEGRATION_NAME = "Bulk-Case-Closer"
JOB_SCRIPT_NAME = "Bulk Case Closer Job"

def close_cases_bulk(siemplify, close_url, api_key, case_ids):
    if not case_ids:
        return
        
    siemplify.LOGGER.info(f"Attempting to close {len(case_ids)} cases in bulk...")
    headers = {
        "AppKey": api_key,
        "accept": "application/json",
        "content-type": "application/json"
    }
    
    current_batch = list(case_ids)
    
    while current_batch:
        payload = {
            "casesIds": current_batch,
            "closeReason": 1, # NotMalicious
            "rootCause": "Stale cases older than configured days",
            "closeComment": "Closed automatically by SOAR Job"
        }
        
        try:
            response = requests.post(close_url, headers=headers, json=payload, verify=False, timeout=60)
            siemplify.LOGGER.info(f"Close Status: {response.status_code}")
            
            if response.status_code == 200:
                siemplify.LOGGER.info(f"Successfully closed {len(current_batch)} cases.")
                break # Done with this batch
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('errorMessage', '')
                    
                    match = re.search(r"Case (\d+) is closed", error_msg)
                    if match:
                        closed_case_id = int(match.group(1))
                        siemplify.LOGGER.info(f"Case {closed_case_id} is already closed. Removing and retrying...")
                        if closed_case_id in current_batch:
                            current_batch.remove(closed_case_id)
                        else:
                            siemplify.LOGGER.warning(f"Case {closed_case_id} was not in current batch.")
                            break
                    else:
                        siemplify.LOGGER.error("Failed to close cases with 400, but couldn't identify specific closed case.")
                        siemplify.LOGGER.error(response.text)
                        break
                except Exception as e:
                    siemplify.LOGGER.error(f"Error parsing error response: {e}")
                    siemplify.LOGGER.error(response.text)
                    break
            elif response.status_code == 504:
                siemplify.LOGGER.warning("Received 504 Gateway Timeout. Waiting 5s and retrying this batch...")
                time.sleep(5)
            else:
                siemplify.LOGGER.error(f"Failed to close cases. Status: {response.status_code}")
                siemplify.LOGGER.error(response.text)
                break
                
        except requests.exceptions.Timeout:
            siemplify.LOGGER.warning("Client timeout. Server took too long. Retrying batch after 5s...")
            time.sleep(5)
        except Exception as e:
            siemplify.LOGGER.error(f"Error during bulk close: {e}")
            break

def main():
    siemplify = SiemplifyJob()
    siemplify.script_name = JOB_SCRIPT_NAME
    
    siemplify.LOGGER.info("Starting Bulk Case Closer Job...")
    
    # Extract Job Parameters (Moved from integration level)
    soar_url = extract_action_param(
        siemplify=siemplify,
        param_name="SOAR URL",
        input_type=str,
        print_value=True,
    )
    api_key = extract_action_param(
        siemplify=siemplify,
        param_name="SOAR API key",
        input_type=str,
        print_value=False, # Don't print sensitive key
    )
    
    # Extract Job Parameter (Existing)
    days_backwards = extract_action_param(
        siemplify=siemplify,
        param_name="Days Backwards",
        input_type=str,
        print_value=True,
        default_value="90",
    )
    
    try:
        days_backwards = int(days_backwards)
    except ValueError:
        siemplify.LOGGER.error("Days Backwards must be an integer. Using default 90.")
        days_backwards = 90
        
    headers = {
        "AppKey": api_key,
        "accept": "application/json",
        "content-type": "application/json"
    }
    
    # Calculate cutoff time
    ninety_days_ago = datetime.utcnow() - timedelta(days=days_backwards)
    end_time_iso = ninety_days_ago.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    
    # Start time a long time ago
    start_time_iso = "2000-01-01T00:00:00.000Z"
    
    search_url = f"{soar_url.rstrip('/')}/api/external/v1/search/CaseSearchEverything"
    close_url = f"{soar_url.rstrip('/')}/api/external/v1/cases-queue/bulk-operations/ExecuteBulkCloseCase"
    
    page_size = 100
    current_page = 0
    total_closed = 0
    
    siemplify.LOGGER.info(f"Searching and closing open cases created before {end_time_iso}...")
    
    try:
        while True:
            payload = {
                "timeRangeFilter": 0, # CUSTOM
                "startTime": start_time_iso,
                "endTime": end_time_iso,
                "isCaseClosed": False, # Only open cases
                "pageSize": page_size,
                "requestedPage": current_page,
                "environments": []
            }
            
            siemplify.LOGGER.info(f"Fetching page {current_page}...")
            response = requests.post(search_url, headers=headers, json=payload, verify=False)
            
            if response.status_code != 200:
                siemplify.LOGGER.error(f"Error searching on page {current_page}: {response.status_code}")
                siemplify.LOGGER.error(response.text)
                break
                
            data = response.json()
            results = data.get('results', [])
            
            siemplify.LOGGER.info(f"Found {len(results)} cases on page {current_page}.")
            
            if not results:
                siemplify.LOGGER.info("No more open cases found.")
                break
                
            # Extract IDs
            case_ids = [case.get('id') for case in results]
            
            if case_ids:
                cases_to_close = list(case_ids)
                cases_to_close.reverse() # Respect bottom up preference within page
                
                close_cases_bulk(siemplify, close_url, api_key, cases_to_close)
                total_closed += len(cases_to_close)
                
            current_page += 1
            time.sleep(1) # Give the server a breather
            
        siemplify.LOGGER.info(f"Finished. Total cases processed/closed in this run: {total_closed}")
            
    except Exception as e:
        siemplify.LOGGER.error(f"Error: {e}")
        
    siemplify.end_script()

if __name__ == "__main__":
    main()
