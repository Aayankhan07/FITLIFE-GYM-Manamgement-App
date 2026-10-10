import unittest
from database.connection import test_connection, initialize_pool
from services.member_service import get_all_members, get_member_by_id

class TestMemberService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initialize connection pool prior to DB service tests."""
        test_connection()
        try:
            initialize_pool()
        except Exception:
            pass

    def test_get_all_members(self):
        """Test retrieving members list."""
        members = get_all_members()
        self.assertIsInstance(members, list)

    def test_get_member_by_id(self):
        """Test retrieving member by ID."""
        member = get_member_by_id(1)
        if member is not None:
            # Row tuple/dict access: element 0 is id
            member_id = member[0] if isinstance(member, (tuple, list)) else member["id"]
            self.assertEqual(member_id, 1)

if __name__ == "__main__":
    unittest.main()
