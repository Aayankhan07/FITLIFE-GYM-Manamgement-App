"""
FitLife — Equipment Service
Inventory CRUD, condition tracking, maintenance alerts.
"""
import logging
from typing import Optional
from database.connection import DatabaseConnection
from config.constants import EQUIPMENT_CATEGORIES, EQUIPMENT_CONDITIONS

logger = logging.getLogger(__name__)


def _log_audit(user_id, action, record_id, detail=""):
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "INSERT INTO audit_logs(user_id,action,module,record_id,new_value,timestamp)"
                " VALUES(?,?,?,?,?,GETDATE())",
                (user_id, action, "Equipment", record_id, detail)
            )
    except Exception as e:
        logger.error(f"Audit error: {e}")


def get_all_equipment(branch_id: Optional[int] = None,
                       category: Optional[str] = None,
                       status: Optional[str] = None,
                       search: Optional[str] = None) -> list:
    try:
        sql = """
            SELECT e.id,
                   e.name,
                   e.category,
                   e.quantity,
                   e.purchase_date,
                   e.purchase_price,
                   e.status,
                   ISNULL(b.branch_name, 'N/A') AS branch_name,
                   e.branch_id
            FROM   equipment e
            LEFT JOIN branches b ON e.branch_id = b.id
            WHERE  1=1
        """
        params = []
        if branch_id:
            sql += " AND e.branch_id=?"
            params.append(branch_id)
        if category:
            sql += " AND e.category=?"
            params.append(category)
        if status:
            sql += " AND e.status=?"
            params.append(status)
        if search:
            sql += " AND (e.name LIKE ?)"
            params.append(f"%{search}%")
        sql += " ORDER BY e.name"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params if params else [])
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_all_equipment error: {e}")
        return []


def get_equipment_by_id(equip_id: int) -> Optional[object]:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                SELECT e.id, e.branch_id, e.name, e.category,
                       e.quantity, e.purchase_date, e.purchase_price,
                       e.status, e.condition, e.next_maintenance_date,
                       b.branch_name
                FROM   equipment e
                JOIN   branches b ON e.branch_id=b.id
                WHERE  e.id=?
            """, (equip_id,))
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"get_equipment_by_id error: {e}")
        return None


def create_equipment(data: dict, created_by: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                INSERT INTO equipment
                    (branch_id, name, category, quantity, purchase_date, purchase_price,
                     status, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,GETDATE(),GETDATE())
            """, (
                data["branch_id"], data["name"],
                data.get("category", "Strength"), data.get("quantity", 1),
                data.get("purchase_date"), data.get("purchase_price"),
                data.get("status", "Active")
            ))
            cursor.execute("SELECT @@IDENTITY")
            new_id = int(cursor.fetchone()[0])
        _log_audit(created_by, "CREATE", new_id, data["name"])
        return {"success": True, "equip_id": new_id, "message": "Equipment added."}
    except Exception as e:
        logger.error(f"create_equipment error: {e}", exc_info=True)
        return {"success": False, "message": f"Failed to add equipment: {e}"}


def update_equipment(equip_id: int, data: dict, updated_by: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("""
                UPDATE equipment SET
                    branch_id=?, name=?, category=?, quantity=?,
                    purchase_date=?, purchase_price=?, status=?,
                    updated_at=GETDATE()
                WHERE id=?
            """, (
                data["branch_id"], data["name"],
                data.get("category", "Strength"), data.get("quantity", 1),
                data.get("purchase_date"), data.get("purchase_price"),
                data.get("status", "Active"), equip_id
            ))
        _log_audit(updated_by, "UPDATE", equip_id, data["name"])
        return {"success": True, "message": "Equipment updated."}
    except Exception as e:
        logger.error(f"update_equipment error: {e}")
        return {"success": False, "message": str(e)}


def delete_equipment(equip_id: int, deleted_by: int) -> dict:
    try:
        row = get_equipment_by_id(equip_id)
        name = row[2] if row else str(equip_id)
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("DELETE FROM equipment WHERE id=?", (equip_id,))
        _log_audit(deleted_by, "DELETE", equip_id, name)
        return {"success": True, "message": f"Equipment '{name}' deleted."}
    except Exception as e:
        logger.error(f"delete_equipment error: {e}")
        return {"success": False, "message": str(e)}


def log_maintenance(equip_id: int, maint_date, notes: str, logged_by: int) -> dict:
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "UPDATE equipment SET last_maintenance_date=?, notes=?, updated_at=GETDATE() WHERE id=?",
                (maint_date, notes, equip_id)
            )
        _log_audit(logged_by, "MAINTENANCE", equip_id, f"Date={maint_date}")
        return {"success": True, "message": "Maintenance date updated."}
    except Exception as e:
        logger.error(f"log_maintenance error: {e}")
        return {"success": False, "message": str(e)}


def get_equipment_stats(branch_id: Optional[int] = None) -> dict:
    try:
        sql = """
            SELECT
                SUM(quantity) AS total_items,
                SUM(CASE WHEN COALESCE(NULLIF(condition_status,''),condition,'') IN ('Good','New')
                         THEN quantity ELSE 0 END) AS in_good_shape,
                SUM(CASE WHEN COALESCE(NULLIF(condition_status,''),condition,'')='Damaged'
                         THEN quantity ELSE 0 END) AS damaged,
                COUNT(DISTINCT id) AS unique_types,
                ISNULL(SUM(purchase_price * quantity),0) AS total_value
            FROM equipment WHERE 1=1
        """
        params = []
        if branch_id:
            sql += " AND branch_id=?"
            params.append(branch_id)
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            row = cursor.fetchone()
            return {
                "total_items":   row[0] or 0,
                "in_good_shape": row[1] or 0,
                "damaged":       row[2] or 0,
                "unique_types":  row[3] or 0,
                "total_value":   float(row[4] or 0),
            }
    except Exception as e:
        logger.error(f"get_equipment_stats error: {e}")
        return {"total_items":0,"in_good_shape":0,"damaged":0,"unique_types":0,"total_value":0}


def get_maintenance_due(days_overdue: int = 90, branch_id: Optional[int] = None) -> list:
    """Equipment not maintained in `days_overdue` days."""
    try:
        sql = """
            SELECT e.id, e.equipment_name, e.category, e.last_maintenance_date,
                   DATEDIFF(day, e.last_maintenance_date, GETDATE()) AS days_since,
                   b.branch_name
            FROM   equipment e
            JOIN   branches b ON e.branch_id=b.id
            WHERE  (e.last_maintenance_date IS NULL
                   OR DATEDIFF(day, e.last_maintenance_date, GETDATE()) > ?)
        """
        params = [days_overdue]
        if branch_id:
            sql += " AND e.branch_id=?"
            params.append(branch_id)
        sql += " ORDER BY days_since DESC"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"get_maintenance_due error: {e}")
        return []
