"""Schema inspection script — initializes pool then queries INFORMATION_SCHEMA."""
import sys
sys.path.insert(0, r'c:\Users\HP\OneDrive\Desktop\FitLife')

from database.connection import initialize_pool, DatabaseConnection

print("Initializing DB pool...")
ok = initialize_pool()
if not ok:
    print("Could not connect to DB!")
    sys.exit(1)

tables = ['equipment', 'salary_records', 'progress_logs', 'members', 'trainers', 'attendance']
for table in tables:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS "
                "WHERE TABLE_NAME=? ORDER BY ORDINAL_POSITION",
                (table,)
            )
            cols = cursor.fetchall()
        if cols:
            print(f"\n=== {table} ({len(cols)} cols) ===")
            for c in cols:
                print(f"  {c[0]}  ({c[1]})")
        else:
            print(f"\n=== {table} — TABLE NOT FOUND ===")
    except Exception as e:
        print(f"Error checking {table}: {e}")
