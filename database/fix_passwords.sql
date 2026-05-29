-- Fix password hashes for all users
-- Run after seed_data.sql if bcrypt hashes are incorrect
USE FitLifeDB;
GO

DECLARE @admin_hash NVARCHAR(255) = '$2b$12$Wv2QNtvXvul3tIFdr22t8edVKNPO5NSXmYmLweTjJcp/tBfokK3Ba'
DECLARE @mgr_hash   NVARCHAR(255) = '$2b$12$9M6HykgoHPNpTQmRbcvxje4QcAaPCGbAlKJpuV7atDsS2xkqw337S'
DECLARE @trainer_hash NVARCHAR(255) = '$2b$12$A6qpNjj29IO9gDdTMDGxh.1lIBbDUEr0uMK79Rfms6c3gNz65YSfm'
DECLARE @member_hash  NVARCHAR(255) = '$2b$12$6vaZsPYA3k4sx4eVcLEgeOCWMEtMUAoPeKF47xTREG/hxJEH3g86u'

UPDATE users SET password_hash = @admin_hash   WHERE username = 'admin';
UPDATE users SET password_hash = @mgr_hash     WHERE username IN ('manager1', 'manager2');
UPDATE users SET password_hash = @trainer_hash WHERE username IN ('trainer1', 'trainer2', 'trainer3', 'trainer4');
UPDATE users SET password_hash = @member_hash  WHERE username IN ('member1', 'member2', 'member3', 'member4', 'member5');

PRINT 'Password hashes updated successfully.';
PRINT 'Credentials: admin/Admin@123, manager1/Manager@123, trainer1/Trainer@123, member1/Member@123';
GO
