# =========================================================
# SmartLine User Account Migration - PowerShell Script
# =========================================================
# This script runs the user_account migration on Windows
# =========================================================

Write-Host ""
Write-Host "=========================================="
Write-Host "SmartLine User Account Migration"
Write-Host "=========================================="
Write-Host ""

# Set your database connection details
$PGHOST = "shuttle.proxy.rlwy.net"
$PGPORT = "47774"
$PGDATABASE = "railway"
$PGUSER = "postgres"
$PGPASSWORD = "your_password_here"  # REPLACE THIS!

# Set environment variables for psql
$env:PGHOST = $PGHOST
$env:PGPORT = $PGPORT
$env:PGDATABASE = $PGDATABASE
$env:PGUSER = $PGUSER
$env:PGPASSWORD = $PGPASSWORD

Write-Host "Connection Details:"
Write-Host "  Host: $PGHOST"
Write-Host "  Port: $PGPORT"
Write-Host "  Database: $PGDATABASE"
Write-Host "  User: $PGUSER"
Write-Host ""

# Check if psql is available
try {
    $psqlVersion = psql --version
    Write-Host "✓ psql found: $psqlVersion"
    Write-Host ""
} catch {
    Write-Host "✗ ERROR: psql not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install PostgreSQL client tools:"
    Write-Host "  1. Download from: https://www.postgresql.org/download/windows/"
    Write-Host "  2. Or install via chocolatey: choco install postgresql"
    Write-Host ""
    exit 1
}

# Confirm before proceeding
Write-Host "⚠️  IMPORTANT: This will modify your database schema!" -ForegroundColor Yellow
Write-Host ""
Write-Host "This migration will:"
Write-Host "  1. Create user_account table"
Write-Host "  2. Create test user (t.gurley1@outlook.com / test / test)"
Write-Host "  3. Add 7 foreign key constraints"
Write-Host "  4. Create 3 new views"
Write-Host ""

$confirmation = Read-Host "Do you want to proceed? (yes/no)"
if ($confirmation -ne "yes") {
    Write-Host ""
    Write-Host "Migration cancelled." -ForegroundColor Yellow
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "=========================================="
Write-Host "Step 1: Creating backup..."
Write-Host "=========================================="
Write-Host ""

$backupFile = "backup_before_user_account_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql"
Write-Host "Creating backup: $backupFile"

try {
    pg_dump --no-owner --no-acl -f $backupFile
    Write-Host "✓ Backup created successfully!" -ForegroundColor Green
    Write-Host "  Location: $(Get-Location)\$backupFile"
    Write-Host ""
} catch {
    Write-Host "✗ Backup failed!" -ForegroundColor Red
    Write-Host "  Error: $_"
    Write-Host ""
    Write-Host "Do you want to continue anyway? (yes/no)"
    $continueAnyway = Read-Host
    if ($continueAnyway -ne "yes") {
        exit 1
    }
}

Write-Host "=========================================="
Write-Host "Step 2: Running migration..."
Write-Host "=========================================="
Write-Host ""

try {
    # Run the migration script
    psql -f add_user_account_windows.sql
    
    Write-Host ""
    Write-Host "✓ Migration completed successfully!" -ForegroundColor Green
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "✗ Migration failed!" -ForegroundColor Red
    Write-Host "  Error: $_"
    Write-Host ""
    Write-Host "You can restore from backup:"
    Write-Host "  psql -f $backupFile"
    Write-Host ""
    exit 1
}

Write-Host "=========================================="
Write-Host "Step 3: Verification..."
Write-Host "=========================================="
Write-Host ""

Write-Host "Verifying user_account table..."
psql -c "SELECT COUNT(*) as user_count FROM user_account;"

Write-Host ""
Write-Host "Verifying foreign keys..."
psql -c "SELECT COUNT(*) as fk_count FROM information_schema.table_constraints WHERE constraint_type = 'FOREIGN KEY' AND constraint_name LIKE 'fk_%_user_id';"

Write-Host ""
Write-Host "=========================================="
Write-Host "Migration Complete!"
Write-Host "=========================================="
Write-Host ""
Write-Host "✓ user_account table created"
Write-Host "✓ Test user created"
Write-Host "✓ Foreign keys added"
Write-Host "✓ Views created"
Write-Host ""
Write-Host "Your Login Credentials:" -ForegroundColor Cyan
Write-Host "  Email: t.gurley1@outlook.com"
Write-Host "  Username: test"
Write-Host "  Password: test"
Write-Host ""
Write-Host "Backup saved to: $backupFile" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Test login with credentials above"
Write-Host "  2. Update your application code"
Write-Host "  3. Review USER_ACCOUNT_MIGRATION.md for details"
Write-Host ""

# Clean up environment variables
Remove-Item Env:PGHOST
Remove-Item Env:PGPORT
Remove-Item Env:PGDATABASE
Remove-Item Env:PGUSER
Remove-Item Env:PGPASSWORD

Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
