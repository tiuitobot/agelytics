"""Agelytics CLI — AoE2 DE replay analyzer."""

import argparse
import glob
import os
import sys

from . import __version__
from .parser import parse_replay
from .db import get_db, insert_match, get_last_match, get_match_by_id, get_player_stats, count_matches
from .report import match_report, player_summary


def cmd_ingest(args):
    """Ingest replay file(s) into the database."""
    conn = get_db(args.db)
    
    files = []
    target = args.path
    if os.path.isdir(target):
        files = sorted(glob.glob(os.path.join(target, "*.aoe2record")))
    elif os.path.isfile(target):
        files = [target]
    else:
        print(f"Error: {target} not found", file=sys.stderr)
        return 1

    total = len(files)
    ok = 0
    skipped = 0
    dupes = 0
    failed = 0

    for i, f in enumerate(files, 1):
        fname = os.path.basename(f)
        match = parse_replay(f)
        if match is None:
            skipped += 1
            if args.verbose:
                print(f"  [{i}/{total}] SKIP {fname}")
            continue
        
        match_id = insert_match(conn, match)
        if match_id is None:
            dupes += 1
            if args.verbose:
                print(f"  [{i}/{total}] DUPE {fname}")
        else:
            ok += 1
            if args.verbose:
                winner = next((p["name"] for p in match["players"] if p["winner"]), "?")
                print(f"  [{i}/{total}] OK   {fname} → #{match_id} ({winner} won)")

    conn.close()
    
    print(f"\nAgelytics ingest: {total} files")
    print(f"  ✅ Ingested: {ok}")
    print(f"  ♻️  Duplicates: {dupes}")
    print(f"  ⏭️  Skipped (SP/error): {skipped}")
    print(f"  ❌ Failed: {failed}")
    
    return 0


def cmd_report(args):
    """Show a match report."""
    conn = get_db(args.db)
    
    if args.match_id:
        match = get_match_by_id(conn, args.match_id)
        if not match:
            print(f"Match #{args.match_id} not found.", file=sys.stderr)
            return 1
    else:
        match = get_last_match(conn)
        if not match:
            print("No matches in database. Run 'ingest' first.", file=sys.stderr)
            return 1
    
    print(match_report(match, player_name=args.player))
    conn.close()
    return 0


def cmd_stats(args):
    """Show player statistics."""
    conn = get_db(args.db)
    stats = get_player_stats(conn, args.player)
    print(player_summary(stats))
    conn.close()
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="agelytics",
        description="AoE2 DE replay analyzer"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--db", default=None, help="Path to SQLite database")
    
    subs = parser.add_subparsers(dest="command")
    
    # ingest
    p_ingest = subs.add_parser("ingest", help="Ingest replay files")
    p_ingest.add_argument("path", help="Replay file or directory")
    p_ingest.add_argument("-v", "--verbose", action="store_true")
    
    # report
    p_report = subs.add_parser("report", help="Show match report")
    p_report.add_argument("--last", action="store_true", default=True)
    p_report.add_argument("--id", dest="match_id", type=int, help="Match ID")
    p_report.add_argument("--player", "-p", default=None, help="Player perspective")
    
    # stats
    p_stats = subs.add_parser("stats", help="Player statistics")
    p_stats.add_argument("player", help="Player name")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    if args.command == "ingest":
        return cmd_ingest(args)
    elif args.command == "report":
        return cmd_report(args)
    elif args.command == "stats":
        return cmd_stats(args)


if __name__ == "__main__":
    sys.exit(main() or 0)
