"""Check equipment name situation in DB."""
import sys
sys.path.insert(0, r'c:\Users\HP\OneDrive\Desktop\FitLife')
from database.connection import initialize_pool, DatabaseConnection

initialize_pool()
with DatabaseConnection() as (conn, cursor):
    cursor.execute(
        "SELECT TOP 5 id, name, equipment_name, category, condition, condition_status "
        "FROM equipment ORDER BY id"
    )
    rows = cursor.fetchall()
    for r in rows:
        print(f"id={r[0]}, name='{r[1]}', equip_name='{r[2]}', cat={r[3]}, cond='{r[4]}', cond_status='{r[5]}'")
