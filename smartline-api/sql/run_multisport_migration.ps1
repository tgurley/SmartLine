# =========================================================
# SmartLine Multi-Sport Migration - PowerShell Runner
# =========================================================
# This script runs all 3 migration steps
# =========================================================

Write-Host ""
Write-Host "=========================================="
Write-Host "SmartLine Multi-Sport Migration"
Write-Host "Version 5.2.0 -> 5.3.0"
Write-Host "=========================================="
Write-Host ""

# Set your database connection details
$PGHOST = "shuttle.proxy.rlwy.net"
$PGPORT = "47774"
$PGDATABASE = "railway"
$PGUSER = "postgres"
$PGPASSWORD = "ygheNUaqHtcfNNAPEpgQgmaBKIKbDlAK"  # REPLACE THIS!

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
    Write-Host "[OK] psql found: $psqlVersion"
    Write-Host ""
} catch {
    Write-Host "[ERROR] psql not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install PostgreSQL client tools:"
    Write-Host "  1. Download from: https://www.postgresql.org/download/windows/"
    Write-Host "  2. Or install via chocolatey: choco install postgresql"
    Write-Host ""
    exit 1
}

# Confirm before proceeding
Write-Host "WARNING: This will modify your database schema!" -ForegroundColor Yellow
Write-Host ""
Write-Host "This migration will:"
Write-Host "  1. Add sport_type, sport_position, sport_stat_type tables"
Write-Host "  2. Add sport_id columns to league, team, player, game, bets"
Write-Host "  3. Set all existing data to sport_id = 1 (NFL)"
Write-Host "  4. Make sport_id required and add foreign keys"
Write-Host "  5. Create new multi-sport views"
Write-Host ""
Write-Host "This enables support for:"
Write-Host "  [+] NFL (existing)"
Write-Host "  [+] NCAAF"
Write-Host "  [+] NBA"
Write-Host "  [+] NCAAB"
Write-Host "  [+] MLB"
Write-Host "  [+] NHL"
Write-Host "  [+] MLS"
Write-Host "  [+] European Soccer (EPL, La Liga, Bundesliga, etc.)"
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
Write-Host "Creating Backup..."
Write-Host "=========================================="
Write-Host ""

$backupFile = "backup_before_multisport_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql"
Write-Host "Creating backup: $backupFile"

try {
    pg_dump --no-owner --no-acl -f $backupFile
    Write-Host "[OK] Backup created successfully!" -ForegroundColor Green
    Write-Host "  Location: $(Get-Location)\$backupFile"
    Write-Host ""
} catch {
    Write-Host "[ERROR] Backup failed!" -ForegroundColor Red
    Write-Host "  Error: $_"
    Write-Host ""
    Write-Host "Do you want to continue anyway? (yes/no)"
    $continueAnyway = Read-Host
    if ($continueAnyway -ne "yes") {
        exit 1
    }
}

# =========================================================
# STEP 1: Add Sport Infrastructure
# =========================================================

Write-Host "=========================================="
Write-Host "Step 1: Adding Sport Infrastructure"
Write-Host "=========================================="
Write-Host ""

try {
    psql -f migration_step1_add_sport_infrastructure.sql
    Write-Host ""
    Write-Host "[OK] Step 1 completed successfully!" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host ""
    Write-Host "[ERROR] Step 1 failed!" -ForegroundColor Red
    Write-Host "  Error: $_"
    Write-Host ""
    Write-Host "You can restore from backup:"
    Write-Host "  psql -f $backupFile"
    Write-Host ""
    exit 1
}

# =========================================================
# STEP 2: Migrate NFL Data
# =========================================================

Write-Host "=========================================="
Write-Host "Step 2: Migrating NFL Data"
Write-Host "=========================================="
Write-Host ""

try {
    psql -f migration_step2_migrate_nfl_data.sql
    Write-Host ""
    Write-Host "[OK] Step 2 completed successfully!" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host ""
    Write-Host "[ERROR] Step 2 failed!" -ForegroundColor Red
    Write-Host "  Error: $_"
    Write-Host ""
    Write-Host "You can restore from backup:"
    Write-Host "  psql -f $backupFile"
    Write-Host ""
    exit 1
}

# =========================================================
# STEP 3: Add Constraints and Views
# =========================================================

Write-Host "=========================================="
Write-Host "Step 3: Adding Constraints and Views"
Write-Host "=========================================="
Write-Host ""

try {
    psql -f migration_step3_add_constraints.sql
    Write-Host ""
    Write-Host "[OK] Step 3 completed successfully!" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host ""
    Write-Host "[ERROR] Step 3 failed!" -ForegroundColor Red
    Write-Host "  Error: $_"
    Write-Host ""
    Write-Host "You can restore from backup:"
    Write-Host "  psql -f $backupFile"
    Write-Host ""
    exit 1
}

# =========================================================
# FINAL VERIFICATION
# =========================================================

Write-Host "=========================================="
Write-Host "Final Verification"
Write-Host "=========================================="
Write-Host ""

Write-Host "Checking sport types..."
$query1 = "SELECT sport_code, sport_name, is_active FROM sport_type ORDER BY display_order;"
psql -c $query1

Write-Host ""
Write-Host "Checking data migration..."
$query2 = "SELECT st.sport_code, st.sport_name, COUNT(l.league_id) as leagues, (SELECT COUNT(*) FROM team WHERE sport_id = st.sport_id) as teams, (SELECT COUNT(*) FROM player WHERE sport_id = st.sport_id) as players FROM sport_type st LEFT JOIN league l ON st.sport_id = l.sport_id GROUP BY st.sport_id, st.sport_code, st.sport_name ORDER BY st.sport_id;"
psql -c $query2

Write-Host ""
Write-Host "=========================================="
Write-Host "Migration Complete!"
Write-Host "=========================================="
Write-Host ""
Write-Host "[OK] Sport infrastructure added"
Write-Host "[OK] NFL data migrated (sport_id = 1)"
Write-Host "[OK] Constraints and foreign keys added"
Write-Host "[OK] Multi-sport views created"
Write-Host ""
Write-Host "Your database is now v5.3.0 - Multi-Sport Ready!" -ForegroundColor Cyan
Write-Host ""
Write-Host "Supported Sports:"
Write-Host "  [+] NFL (National Football League)"
Write-Host "  [+] NCAAF (NCAA Football)"
Write-Host "  [+] NBA (National Basketball Association)"
Write-Host "  [+] NCAAB (NCAA Basketball)"
Write-Host "  [+] MLB (Major League Baseball)"
Write-Host "  [+] NHL (National Hockey League)"
Write-Host "  [+] MLS (Major League Soccer)"
Write-Host "  [+] EPL (English Premier League)"
Write-Host "  [+] La Liga, Bundesliga, Serie A, Ligue 1"
Write-Host "  [+] UEFA Champions League"
Write-Host ""
Write-Host "Backup saved to: $backupFile" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Update your ETL scripts to use sport_code parameter"
Write-Host "  2. Start adding data for other sports"
Write-Host "  3. Use sport-specific views: v_nfl_player_odds, v_nba_player_odds, etc."
Write-Host "  4. Filter by sport: SELECT * FROM game WHERE sport_id = 3 (NBA)"
Write-Host ""
Write-Host "Run 'pg_dump --schema-only' to generate updated schema_v5.3.0.sql"
Write-Host ""

# Clean up environment variables
Remove-Item Env:PGHOST
Remove-Item Env:PGPORT
Remove-Item Env:PGDATABASE
Remove-Item Env:PGUSER
Remove-Item Env:PGPASSWORD

Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
