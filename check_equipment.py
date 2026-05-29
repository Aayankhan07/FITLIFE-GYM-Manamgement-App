"""Check equipment and member data."""
import sys
sys.path.insert(0, r"c:\Users\HP\OneDrive\Desktop\FitLife")
from database.connection import initialize_pool, DatabaseConnection

ok = initialize_pool()
if not ok:
    print("DB pool init failed")
    sys.exit(1)

with DatabaseConnection() as (conn, cursor):
    # Show all equipment data
    cursor.execute("SELECT id, name, equipment_name, category, condition, condition_status, quantity, branch_id FROM equipment")
    rows = cursor.fetchall()
    print("All equipment:")
    for r in rows:
        print(f"  id={r[0]}, name='{r[1]}', equip_name='{r[2]}', cat={r[3]}, cond={r[4]}, cond_stat={r[5]}, qty={r[6]}, branch={r[7]}")
    
    # Show members
    cursor.execute("SELECT id, full_name, status FROM members")
    rows2 = cursor.fetchall()
    print("\nMembers:")
    for r in rows2:
        print(f"  {r[0]}: {r[1]} ({r[2]})")
    
    # Check current get_all_equipment query output
    cursor.execute("""
        SELECT e.id,
               ISNULL(e.equipment_name, e.name) AS equipment_name,
               e.category,
               ISNULL(e.brand, '') AS brand,
               ISNULL(e.model, '') AS model,
               ISNULL(e.serial_number, '') AS serial_number,
               ISNULL(e.condition_status, e.condition) AS condition_status,
               e.purchase_date,
               e.purchase_price,
               e.last_maintenance_date,
               '' AS notes,
               ISNULL(b.branch_name, 'N/A') AS branch_name,
               e.branch_id,
               e.quantity
        FROM equipment e
        LEFT JOIN branches b ON e.branch_id = b.id
        WHERE 1=1
        ORDER BY ISNULL(e.equipment_name, e.name)
    """)
    rows3 = cursor.fetchall()
    print(f"\nEquipment query returns {len(rows3)} rows")
    for r in rows3:
        print(f"  id={r[0]}, name='{r[1]}', cat={r[2]}, qty={r[13]}, cond={r[6]}, branch='{r[11]}'")
