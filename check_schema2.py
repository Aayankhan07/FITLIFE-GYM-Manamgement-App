from database.connection import DatabaseConnection
with DatabaseConnection() as (conn, cursor):
    cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='equipment' ORDER BY ORDINAL_POSITION")
    rows = cursor.fetchall()
    print("Equipment columns:")
    for r in rows:
        print(" -", r[0])
    
    # Also count rows
    cursor.execute("SELECT COUNT(*) FROM equipment")
    cnt = cursor.fetchone()[0]
    print(f"\nTotal equipment rows: {cnt}")
    
    # Also check members
    cursor.execute("SELECT COUNT(*) FROM members WHERE status='Active'")
    mcnt = cursor.fetchone()[0]
    print(f"Active members: {mcnt}")
    
    # Check progress_logs table
    cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='progress_logs' ORDER BY ORDINAL_POSITION")
    rows2 = cursor.fetchall()
    print("\nProgress_logs columns:")
    for r in rows2:
        print(" -", r[0])
