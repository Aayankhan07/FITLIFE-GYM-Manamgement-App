import unittest
from datetime import datetime
from database.connection import test_connection, initialize_pool
from services.billing_service import get_branch_financials, generate_invoice_number

class TestBillingService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initialize connection pool prior to DB service tests."""
        test_connection()
        try:
            initialize_pool()
        except Exception:
            pass

    def test_generate_invoice_number(self):
        """Test invoice number generation format."""
        inv = generate_invoice_number()
        self.assertTrue(inv.startswith("INV-"))

    def test_get_branch_financials(self):
        """Test retrieving financial metrics summary with required month and year."""
        now = datetime.now()
        summary = get_branch_financials(branch_id=1, month=now.month, year=now.year)
        self.assertIsInstance(summary, dict)

if __name__ == "__main__":
    unittest.main()
