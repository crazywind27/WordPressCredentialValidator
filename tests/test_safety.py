import io
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "VertaBassh"))

import VertaBassh


class SafetyTests(unittest.TestCase):
    def test_parse_hydra_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "hydra.txt"
            path.write_text("[80][http-post-form] host: site login: admin password: secret\n", encoding="utf-8")
            credentials = VertaBassh.parse_hydra_output(path)
        self.assertEqual(credentials[0].username, "admin")
        self.assertEqual(credentials[0].password, "secret")

    def test_url_requires_https_by_default(self):
        with self.assertRaises(ValueError):
            VertaBassh.normalize_login_url("http://example.com/wp-login.php")

    def test_url_requires_wordpress_login_path_by_default(self):
        with self.assertRaises(ValueError):
            VertaBassh.normalize_login_url("https://example.com/login")

    def test_report_redacts_passwords(self):
        output = io.StringIO()
        result = VertaBassh.ValidationResult("admin", "Success", True)
        VertaBassh.write_report(output, "https://example.com/wp-login.php", [result])
        report = output.getvalue()
        self.assertIn("Password: <redacted>", report)
        self.assertNotIn("secret", report)

    def test_authorization_gate_exits_before_network(self):
        exit_code = VertaBassh.run(["-u", "https://example.com/wp-login.php", "-f", "missing.txt"])
        self.assertEqual(exit_code, 2)


if __name__ == "__main__":
    unittest.main()
