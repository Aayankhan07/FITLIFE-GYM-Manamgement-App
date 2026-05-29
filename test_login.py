"""FitLife — Login Test Script"""
import sys
sys.path.insert(0, ".")

from database.connection import initialize_pool
from services.auth_service import login

if not initialize_pool():
    print("FAIL: Pool init failed"); sys.exit(1)

print("Pool initialized OK\n")

tests = [
    ("admin",    "Admin@123",   "Admin"),
    ("manager1", "Manager@123", "Manager"),
    ("trainer1", "Trainer@123", "Trainer"),
    ("member1",  "Member@123",  "Member"),
    ("admin",    "WrongPass",   None),   # None = expect failure
    ("nouser",   "whatever",    None),   # Non-existent user
]

pass_count = 0
fail_count = 0

for username, password, expected_role in tests:
    result = login(username, password)
    if expected_role is None:
        if not result["success"]:
            print(f"  PASS : {username} correctly rejected ({result['message']})")
            pass_count += 1
        else:
            print(f"  FAIL : {username} wrong password was accepted!")
            fail_count += 1
    else:
        if result["success"]:
            session = result.get("session")
            role = getattr(session, "role", "unknown") if session else "no session"
            user = getattr(session, "username", "?") if session else "?"
            print(f"  PASS : {username} -> role={role}, user={user}")
            pass_count += 1
        else:
            print(f"  FAIL : {username} login failed: {result['message']}")
            fail_count += 1

print(f"\nResults: {pass_count} passed, {fail_count} failed out of {len(tests)} tests")
