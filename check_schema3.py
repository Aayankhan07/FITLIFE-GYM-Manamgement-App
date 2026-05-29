"""Check equipment and other table schemas."""
import sys
sys.path.insert(0, r"c:\Users\HP\OneDrive\Desktop\FitLife")
from database.connection import initialize_pool, DatabaseConnection

ok = initialize_pool()
if not ok:
    print("DB pool init failed")
    sys.exit(1)

with DatabaseConnection() as (conn, cursor):
    # Equipment columns
    cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='equipment' ORDER BY ORDINAL_POSITION")
    rows = cursor.fetchall()
    print("Equipment columns:")
    for r in rows: print(" -", r[0])
    
    cursor.execute("SELECT COUNT(*) FROM equipment")
    cnt = cursor.fetchone()[0]
    print(f"\nTotal equipment rows: {cnt}")
    
    cursor.execute("SELECT COUNT(*) FROM members WHERE status='Active'")
    mcnt = cursor.fetchone()[0]
    print(f"Active members: {mcnt}")
    
    # Try fetching equipment with the current query
    try:
        cursor.execute("SELECT TOP 3 id, ISNULL(equipment_name, name) as nm, category, condition_status FROM equipment")
        rows = cursor.fetchall()
        print(f"\nSample equipment: {rows}")
    except Exception as e:
        print(f"Equipment query error: {e}")
    
    # Check progress_logs table
    cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='progress_logs' ORDER BY ORDINAL_POSITION")
    rows2 = cursor.fetchall()
    print("\nProgress_logs columns:")
    for r in rows2: print(" -", r[0])
    
    cursor.execute("SELECT COUNT(*) FROM progress_logs")
    plcnt = cursor.fetchone()[0]
    print(f"Total progress_logs rows: {plcnt}")
