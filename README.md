# VertaBassh - Authorized WordPress Credential Validator

VertaBassh is a defensive helper for validating known WordPress credentials on
systems you own or are explicitly authorized to test. It parses Hydra-style
output, validates each credential against a WordPress login endpoint, and writes
a redacted result report.

This project handles credential material. Do not commit input files, generated
reports, terminal transcripts, or logs that contain usernames or passwords.

## Safety Defaults

- Requires `--i-have-authorization` before any network request is made.
- Requires HTTPS by default.
- Keeps TLS certificate verification enabled by default.
- Restricts the target path to `/wp-login.php` unless explicitly overridden.
- Redacts passwords in console output and result files.
- Stores default reports under the ignored `results/` directory.

## Requirements

- Python 3.9 or later
- `requests`
- `colorama`

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

```bash
python VertaBassh/VertaBassh.py -u https://example.com/wp-login.php -f hydra_output.txt --i-have-authorization
```

Options:

| Argument | Description |
| --- | --- |
| `-u`, `--url` | Authorized WordPress login URL. HTTPS is required by default. |
| `-f`, `--file` | Hydra-style output file containing `login:` and `password:` fields. |
| `-l`, `--limit` | Optional positive limit for the number of credentials to validate. |
| `-o`, `--output` | Optional redacted output file path. Defaults to `results/VertaBassh_results_<timestamp>.txt`. |
| `--i-have-authorization` | Required confirmation that you own or are authorized to test the target. |
| `--insecure` | Lab-only TLS verification bypass. Do not use on untrusted networks. |
| `--allow-http` | Lab-only non-HTTPS URL allowance. |
| `--allow-nonstandard-login-path` | Allows a path other than `/wp-login.php`. |
| `--overwrite` | Allows overwriting an existing output file. |

## Output

Reports intentionally redact passwords:

```text
WordPress Credential Validation Results
Sensitive values are redacted by design.
Target URL: https://example.com/wp-login.php
========================================
Tested username=admin password=<redacted> - Status: Failed

========================================
Total Tests Attempted: 1
Successful Logins: 0
Failed Logins: 1
Connection Errors: 0
========================================
```

Successful usernames may be listed, but passwords remain redacted.

## Historical Exposure

Earlier public history for this repository included generated
`VertaBassh_results_*.txt` files. If any value in those files was real, rotate
the affected credentials and purge or recreate public history so old blobs are
not reachable.

## Tests

```bash
python -m unittest discover -s tests
```

## License

MIT. See `LICENSE`.
