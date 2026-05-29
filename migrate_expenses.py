import sys
import os
sys.path.append(os.getcwd())
from database.connection import DatabaseConnection, initialize_pool

def apply_migration():
    initialize_pool()
    sql = """
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'expenses')
    BEGIN
        CREATE TABLE expenses (
            id             INT IDENTITY(1,1) PRIMARY KEY,
            branch_id      INT           NOT NULL REFERENCES branches(id),
            category       NVARCHAR(100) NOT NULL,
            amount         DECIMAL(10,2) NOT NULL CHECK (amount > 0),
            expense_date   DATE          NOT NULL DEFAULT CAST(GETDATE() AS DATE),
            description    NVARCHAR(500) NULL,
            recorded_by    INT           NULL REFERENCES users(id),
            created_at     DATETIME2     NOT NULL DEFAULT GETDATE()
        );
        PRINT 'Created expenses table';
    END
    ELSE
    BEGIN
        PRINT 'expenses table already exists';
    END
    """
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql)
            conn.commit()
        print("Migration applied successfully.")
    except Exception as e:
        print(f"Error applying migration: {e}")

if __name__ == '__main__':
    apply_migration()
