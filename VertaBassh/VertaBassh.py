import argparse
import random
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

try:
    from colorama import Fore, Style, init
except ImportError:
    class _NoColor:
        BLACK = RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET_ALL = ""

    Fore = Style = _NoColor()

    def init(*_args, **_kwargs):
        return None


VERSION = "1.1.0"
CREDITS = ["@crazywind27"]
DEFAULT_RESULTS_DIR = "results"
DEFAULT_DELAY_RANGE_SECONDS = (5.0, 10.0)
HYDRA_CREDENTIAL_PATTERN = re.compile(r"login:\s*(\S+)\s+password:\s*(\S+)", re.IGNORECASE)


@dataclass(frozen=True)
class Credential:
    username: str
    password: str


@dataclass(frozen=True)
class ValidationResult:
    username: str
    status: str
    success: bool
    note: str = ""


def parse_arguments(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Authorized WordPress credential validation helper",
        usage=(
            "python VertaBassh.py -u <URL> -f <file> --i-have-authorization "
            "[-l <limit>] [-o <output file>] [--insecure]"
        ),
    )
    parser.add_argument("-u", "--url", required=True, help="Authorized WordPress login URL.")
    parser.add_argument("-f", "--file", required=True, help="Hydra output file containing credentials to validate.")
    parser.add_argument("-l", "--limit", type=int, default=None, help="Limit the number of tests to run.")
    parser.add_argument("-o", "--output", help="Custom redacted output file path.")
    parser.add_argument(
        "--i-have-authorization",
        action="store_true",
        help="Required. Confirms you own or are authorized to test the target.",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Lab-only: disable TLS certificate verification. Never use this on untrusted networks.",
    )
    parser.add_argument(
        "--allow-http",
        action="store_true",
        help="Lab-only: allow a non-HTTPS target URL.",
    )
    parser.add_argument(
        "--allow-nonstandard-login-path",
        action="store_true",
        help="Allow a login path other than /wp-login.php.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting an existing output file.",
    )
    return parser.parse_args(list(argv))


def normalize_login_url(raw_url: str, allow_http: bool = False, allow_nonstandard_path: bool = False) -> str:
    parsed = urlparse(raw_url)
    if parsed.scheme not in ("https", "http") or not parsed.netloc:
        raise ValueError("URL must include scheme and host, for example https://example.com/wp-login.php")
    if parsed.scheme != "https" and not allow_http:
        raise ValueError("HTTPS is required unless --allow-http is supplied for a lab target.")
    normalized_path = parsed.path.rstrip("/") or "/"
    if normalized_path != "/wp-login.php" and not allow_nonstandard_path:
        raise ValueError("Target path must be /wp-login.php unless --allow-nonstandard-login-path is supplied.")
    return raw_url


def parse_hydra_output(path: Path, limit: Optional[int] = None) -> List[Credential]:
    if limit is not None and limit <= 0:
        raise ValueError("--limit must be greater than zero.")

    credentials: List[Credential] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            match = HYDRA_CREDENTIAL_PATTERN.search(line)
            if not match:
                continue
            credentials.append(Credential(username=match.group(1), password=match.group(2)))
            if limit is not None and len(credentials) >= limit:
                break
    return credentials


def default_output_path() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path(DEFAULT_RESULTS_DIR) / f"VertaBassh_results_{timestamp}.txt"


def open_output_file(path: Path, overwrite: bool):
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "w" if overwrite else "x"
    return path.open(mode, encoding="utf-8")


def create_session() -> requests.Session:
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET", "POST"]),
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def is_successful_wordpress_login(response: requests.Response) -> bool:
    body = response.text.lower()
    final_path = urlparse(response.url).path.lower()
    return (
        "wp-admin" in final_path
        or "dashboard" in body
        or "wp-admin/profile.php" in body
        or "wp-login.php?action=logout" in body
    )


def validate_credential(
    session: requests.Session,
    login_url: str,
    credential: Credential,
    verify_tls: bool,
) -> ValidationResult:
    payload = {
        "log": credential.username,
        "pwd": credential.password,
        "wp-submit": "Log In",
        "redirect_to": login_url,
        "testcookie": "1",
    }
    headers = {
        "User-Agent": "VertaBassh authorized WordPress credential validator",
    }

    try:
        response = session.post(
            login_url,
            data=payload,
            headers=headers,
            timeout=10,
            verify=verify_tls,
            allow_redirects=True,
        )
    except requests.RequestException as exc:
        return ValidationResult(credential.username, "Connection Error", False, str(exc))

    if is_successful_wordpress_login(response):
        return ValidationResult(credential.username, "Success", True)
    return ValidationResult(credential.username, "Failed", False)


def redacted_result_line(result: ValidationResult) -> str:
    note = f" Note: {result.note}" if result.note else ""
    return f"Tested username={result.username} password=<redacted> - Status: {result.status}{note}"


def write_report(output_handle, target_url: str, results: List[ValidationResult]) -> None:
    successes = [result for result in results if result.success]
    failures = [result for result in results if result.status == "Failed"]
    errors = [result for result in results if result.status == "Connection Error"]

    output_handle.write("WordPress Credential Validation Results\n")
    output_handle.write("Sensitive values are redacted by design.\n")
    output_handle.write(f"Target URL: {target_url}\n")
    output_handle.write("=" * 40 + "\n")
    for result in results:
        output_handle.write(redacted_result_line(result) + "\n")

    output_handle.write("\n" + "=" * 40 + "\n")
    output_handle.write(f"Total Tests Attempted: {len(results)}\n")
    output_handle.write(f"Successful Logins: {len(successes)}\n")
    output_handle.write(f"Failed Logins: {len(failures)}\n")
    output_handle.write(f"Connection Errors: {len(errors)}\n")
    output_handle.write("=" * 40 + "\n")
    if successes:
        output_handle.write("\nSuccessful Usernames Found:\n")
        for result in successes:
            output_handle.write(f"Username: {result.username} Password: <redacted>\n")
        output_handle.write("=" * 40 + "\n")


def display_intro(login_url: str, input_file: Path, output_file: Path, verify_tls: bool) -> None:
    print(f"{Fore.YELLOW}VertaBassh - Authorized WordPress Credential Validator{Style.RESET_ALL}")
    print(f"Version {Fore.GREEN}{VERSION}{Style.RESET_ALL}")
    print(f"Developed by {', '.join(CREDITS)}")
    print(f"{Fore.MAGENTA}Target Site:        {Fore.WHITE}{login_url}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}Input File:         {Fore.WHITE}{input_file}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}Results Output File:{Fore.WHITE} {output_file}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}TLS Verification:   {Fore.WHITE}{'enabled' if verify_tls else 'disabled'}{Style.RESET_ALL}")
    print("Passwords are never printed or written to the results file.")
    print()


def run(argv: Iterable[str]) -> int:
    init(autoreset=True)
    args = parse_arguments(argv)

    if not args.i_have_authorization:
        print("Error: --i-have-authorization is required before any network request is made.", file=sys.stderr)
        return 2

    try:
        login_url = normalize_login_url(args.url, args.allow_http, args.allow_nonstandard_login_path)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    input_file = Path(args.file)
    output_file = Path(args.output) if args.output else default_output_path()
    verify_tls = not args.insecure

    if args.insecure:
        print("Warning: TLS certificate verification is disabled for this run.", file=sys.stderr)

    try:
        credentials = parse_hydra_output(input_file, args.limit)
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if not credentials:
        print("No credentials were found in the input file.", file=sys.stderr)
        return 1

    display_intro(login_url, input_file, output_file, verify_tls)
    results: List[ValidationResult] = []

    try:
        with create_session() as session, open_output_file(output_file, args.overwrite) as handle:
            for index, credential in enumerate(credentials, start=1):
                result = validate_credential(session, login_url, credential, verify_tls)
                results.append(result)
                color = Fore.GREEN if result.success else Fore.RED if result.status == "Failed" else Fore.YELLOW
                print(f"{color}Tested username={credential.username} password=<redacted> - {result.status}{Style.RESET_ALL}")
                if index < len(credentials):
                    time.sleep(random.uniform(*DEFAULT_DELAY_RANGE_SECONDS))
            write_report(handle, login_url, results)
    except FileExistsError:
        print(f"Error: output file already exists: {output_file}. Use --overwrite or choose a new path.", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"Error writing results: {exc}", file=sys.stderr)
        return 2

    print(f"\n{Fore.CYAN}Redacted results saved to {output_file}{Style.RESET_ALL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
