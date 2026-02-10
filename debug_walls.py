#!/usr/bin/env python3
"""Debug script to check for Wall inputs in a replay."""

import sys
from mgz.summary import Summary

if len(sys.argv) < 2:
    print("Usage: python debug_walls.py <replay_file>")
    sys.exit(1)

replay_path = sys.argv[1]

with open(replay_path, "rb") as f:
    s = Summary(f)

match = s.match

if not hasattr(match, "inputs") or not match.inputs:
    print("No inputs found in replay")
    sys.exit(0)

wall_count = 0
for inp in match.inputs:
    if inp.type == "Wall":
        wall_count += 1
        print(f"\n=== Wall Input #{wall_count} ===")
        print(f"Player: {inp.player.name if hasattr(inp.player, 'name') else 'Unknown'}")
        print(f"Timestamp: {inp.timestamp if hasattr(inp, 'timestamp') else 'Unknown'}")
        print(f"Type: {inp.type}")
        
        # Check for payload
        if hasattr(inp, "payload") and inp.payload:
            print(f"Payload: {inp.payload}")
        
        # Check for position attributes
        for attr in dir(inp):
            if not attr.startswith("_") and attr not in ["type", "player", "timestamp", "payload"]:
                value = getattr(inp, attr, None)
                if value is not None:
                    print(f"{attr}: {value}")

if wall_count == 0:
    print("No Wall inputs found in this replay")
else:
    print(f"\nTotal Wall inputs: {wall_count}")
