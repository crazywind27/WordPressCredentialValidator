
# 🌐 VertaBassh - WordPress Credential Validator

VertaBassh is a **Python-based tool** designed to validate WordPress credentials by testing username and password combinations. It processes output from Hydra (or similar tools) and provides a real-time progress indicator, result logging, and error handling.

---

## ✨ Features

- 🔍 **Credential Validation**: Tests WordPress credentials from a list of username-password combinations.
- 💡 **Progress Indicator**: Shows real-time feedback with a processing spinner.
- 📝 **Detailed Logging**: Saves a summary of results, including successful and failed logins, connection errors, and more.
- 🔄 **Connection Retry Logic**: Handles connection errors gracefully.
- ⚙️ **Customizable Options**: Allows setting custom output file names and limiting the number of tests.

---

## 📋 Requirements

- **Python 3.x**
- **requests** library
- **colorama** library for colored output

Install the required libraries with:

```bash
pip install requests colorama
```

---

## 🚀 Usage

### Command-Line Arguments

```bash
python VertaBassh.py -u <URL> -f <file> [-l <limit>] [-o <output file>]
```

| Argument            | Description                                                                                   |
|---------------------|-----------------------------------------------------------------------------------------------|
| `-u` or `--url`    | Target login URL (e.g., `https://example.com/wp-login.php`). **Required**.                    |
| `-f` or `--file`   | Path to the Hydra output file with usernames and passwords. **Required**.                     |
| `-l` or `--limit`  | Limit the number of tests to run. Optional.                                                   |
| `-o` or `--output` | Specify a custom output file for results. If not specified, a timestamped file is created.    |

### Examples

**Basic Usage**:
```bash
python VertaBassh.py -u https://example.com/wp-login.php -f hydra_output.txt
```

**Specify an Output File**:
```bash
python VertaBassh.py -u https://example.com/wp-login.php -f hydra_output.txt -o output_log.txt
```

**Limit the Number of Tests**:
```bash
python VertaBassh.py -u https://example.com/wp-login.php -f hydra_output.txt -l 10
```

---

## 📄 Sample Results Output

After running, the script will save results in the specified output file in the following format:

```
WordPress Credential Validation Script Results
========================================
Total Tests Attempted: 20
Successful Logins: 1
Failed Logins: 19
Connection Errors: 0
========================================

Successful Logins Found:
Username: admin   Password: password123
========================================
```

---

## 🔧 Troubleshooting

- **Connection Errors**: Ensure you have a stable internet connection and that the target site is reachable.
- **URL Formatting**: Verify that the URL points to the correct WordPress login page.
- **Dependencies**: If you encounter errors, confirm that `requests` and `colorama` libraries are installed.

---

## 👥 Credits

- **Developed by**: [@crazywind27](https://github.com/crazywind27)
- **Version**: 1.0.0

---

## 📜 License

This project is open-source and available under the MIT License.

---

Happy testing with **VertaBassh**! 🎉
