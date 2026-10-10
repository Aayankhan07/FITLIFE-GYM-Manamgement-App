import unittest
from utils.health_check import run_health_check, check_packages, check_services

class TestHealthCheck(unittest.TestCase):

    def test_check_packages(self):
        """Verify standard packages import check function."""
        missing = check_packages()
        self.assertIsInstance(missing, list)

    def test_check_services(self):
        """Verify core service modules import checks."""
        failed = check_services()
        self.assertIsInstance(failed, list)

    def test_run_health_check(self):
        """Verify full health check dictionary output structure."""
        res = run_health_check()
        self.assertIsInstance(res, dict)
        self.assertIn("ok", res)
        self.assertIn("missing_packages", res)
        self.assertIn("failed_services", res)
        self.assertIn("db_ok", res)

if __name__ == "__main__":
    unittest.main()
