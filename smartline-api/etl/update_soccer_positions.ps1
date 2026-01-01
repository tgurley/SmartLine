# Update Soccer Players - Re-run ETL to fix positions
# ====================================================
# PowerShell version

Write-Host "======================================================================"
Write-Host "SOCCER PLAYER POSITION FIX" -ForegroundColor Cyan
Write-Host "======================================================================"
Write-Host ""
Write-Host "This will re-run the Soccer ETL to update missing position data."
Write-Host "The ETL has been fixed to extract position from statistics[0].games.position"
Write-Host ""
Write-Host "Expected behavior:"
Write-Host "  - Inserted: 0 (all players already exist)"
Write-Host "  - Updated: ~4,011 (all players get position + normalized height/weight)"
Write-Host "  - Duration: ~5-10 minutes total for all leagues"
Write-Host ""
Write-Host "======================================================================"
Write-Host ""

$continue = Read-Host "Press Enter to continue or Ctrl+C to cancel"

Write-Host ""
Write-Host "🔄 Step 1/7: Updating MLS players..." -ForegroundColor Yellow
python player_etl.py --sport MLS --season 2024 --all

Write-Host ""
Write-Host "🔄 Step 2/7: Updating EPL players..." -ForegroundColor Yellow
python player_etl.py --sport EPL --season 2024 --all

Write-Host ""
Write-Host "🔄 Step 3/7: Updating La Liga players..." -ForegroundColor Yellow
python player_etl.py --sport LA_LIGA --season 2024 --all

Write-Host ""
Write-Host "🔄 Step 4/7: Updating Bundesliga players..." -ForegroundColor Yellow
python player_etl.py --sport BUNDESLIGA --season 2024 --all

Write-Host ""
Write-Host "🔄 Step 5/7: Updating Serie A players..." -ForegroundColor Yellow
python player_etl.py --sport SERIE_A --season 2024 --all

Write-Host ""
Write-Host "🔄 Step 6/7: Updating Ligue 1 players..." -ForegroundColor Yellow
python player_etl.py --sport LIGUE_1 --season 2024 --all

Write-Host ""
Write-Host "🔄 Step 7/7: Updating Champions League players..." -ForegroundColor Yellow
python player_etl.py --sport CHAMPIONS --season 2024 --all

Write-Host ""
Write-Host "======================================================================"
Write-Host "✅ UPDATE COMPLETE!" -ForegroundColor Green
Write-Host "======================================================================"
Write-Host ""
Write-Host "Run this query to verify positions are now populated:"
Write-Host ""
Write-Host "SELECT position, COUNT(*) FROM player" -ForegroundColor Cyan
Write-Host "WHERE sport_id IN (SELECT sport_id FROM sport_type WHERE sport_code IN ('MLS','EPL','LA_LIGA','BUNDESLIGA','SERIE_A','LIGUE_1','CHAMPIONS'))" -ForegroundColor Cyan
Write-Host "GROUP BY position ORDER BY COUNT(*) DESC;" -ForegroundColor Cyan
Write-Host ""
Write-Host "Expected positions: Goalkeeper, Defender, Midfielder, Attacker"
Write-Host ""
