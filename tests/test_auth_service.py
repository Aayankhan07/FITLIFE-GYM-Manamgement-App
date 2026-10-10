import unittest

class TestAuthService(unittest.TestCase):

    def test_password_hashing(self):
        """Verify password hashing logic."""
        try:
            from services.auth_service import hash_password, verify_password
            plain = "SecretPassword123!"
            hashed = hash_password(plain)
            self.assertNotEqual(plain, hashed)
            self.assertTrue(verify_password(plain, hashed))
            self.assertFalse(verify_password("WrongPassword", hashed))
        except ImportError:
            self.skipTest("bcrypt package not installed in global environment")

    def test_login_interface(self):
        """Verify login function availability."""
        from services.auth_service import login
        self.assertTrue(callable(login))

if __name__ == "__main__":
    unittest.main()
