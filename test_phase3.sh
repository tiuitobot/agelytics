#!/bin/bash
# Test script for Phase 3 features

set -e

echo "=== Phase 3 Feature Test ==="
echo ""

cd ~/repos/agelytics
source venv/bin/activate

# Test 1: Ingest a replay with walls
echo "Test 1: Ingesting replay with wall data..."
python -m agelytics --db data/test_phase3.db ingest '/mnt/c/Users/administrador/Games/Age of Empires 2 DE/76561198028659538/savegame/MP Replay v101.103.31214.0 @2026.01.15 083442 (1).aoe2record' -v
echo ""

# Test 2: Check wall data in DB
echo "Test 2: Checking wall data in database..."
sqlite3 data/test_phase3.db "SELECT name, wall_tiles_json FROM match_players WHERE match_id = 1 AND wall_tiles_json IS NOT NULL;"
echo ""

# Test 3: Generate match report with walling section
echo "Test 3: Generating match report..."
python -m agelytics --db data/test_phase3.db report --id 1 | grep -A 5 "Walling"
echo ""

# Test 4: Ingest multiple replays for stats
echo "Test 4: Ingesting additional replays for stats testing..."
python -m agelytics --db data/test_phase3.db ingest '/mnt/c/Users/administrador/Games/Age of Empires 2 DE/76561198028659538/savegame/MP Replay v101.103.31214.0 @2026.01.12 183150 (2).aoe2record' -v
python -m agelytics --db data/test_phase3.db ingest '/mnt/c/Users/administrador/Games/Age of Empires 2 DE/76561198028659538/savegame/MP Replay v101.103.31214.0 @2026.01.15 092910 (1).aoe2record' -v
echo ""

# Test 5: Generate cross-game stats report
echo "Test 5: Generating cross-game stats report..."
python -m agelytics --db data/test_phase3.db stats blzulian
echo ""

# Test 6: Test individual stats functions
echo "Test 6: Testing individual stats functions..."
python -c "
from agelytics.db import get_db
from agelytics.stats import player_stats, win_rate_by_civ, win_rate_by_map

conn = get_db('data/test_phase3.db')

print('=== player_stats() ===')
import json
print(json.dumps(player_stats(conn, 'blzulian'), indent=2))

print('\n=== win_rate_by_civ() ===')
print(json.dumps(win_rate_by_civ(conn, 'blzulian'), indent=2))

print('\n=== win_rate_by_map() ===')
print(json.dumps(win_rate_by_map(conn, 'blzulian'), indent=2))
"

echo ""
echo "=== All Phase 3 Tests Passed! ==="
