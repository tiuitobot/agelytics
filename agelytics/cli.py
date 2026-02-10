"""Agelytics CLI — AoE2 DE replay analyzer."""

import argparse
import glob
import os
import sys

from . import __version__
from .parser import parse_replay
from .db import get_db, insert_match, get_last_match, get_match_by_id, get_player_stats, count_matches, get_all_matches
from .report import match_report, player_summary, matches_table
from .patterns import generate_patterns, format_patterns_text


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
    
    # Handle --all flag (list all matches)
    if args.all:
        if not args.player:
            print("Error: --all requires --player/-p to specify player perspective", file=sys.stderr)
            return 1
        
        matches = get_all_matches(conn, player_name=args.player, limit=args.limit or 50)
        if not matches:
            print(f"No matches found for player '{args.player}'.", file=sys.stderr)
            return 1
        
        print(matches_table(matches, player_name=args.player))
        conn.close()
        return 0
    
    # Handle single match report
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
    from .stats import stats_report
    conn = get_db(args.db)
    print(stats_report(conn, args.player))
    conn.close()
    return 0


def cmd_patterns(args):
    """Generate and display pattern analysis."""
    patterns = generate_patterns(player=args.player, db_path=args.db)
    print(format_patterns_text(patterns))
    return 0


def cmd_pdf(args):
    """Generate PDF report for a match."""
    from .pdf_report import generate_match_pdf
    
    conn = get_db(args.db)
    
    if args.match_id:
        match = get_match_by_id(conn, args.match_id)
        if not match:
            print(f"Match #{args.match_id} not found.", file=sys.stderr)
            conn.close()
            return 1
    else:
        match = get_last_match(conn)
        if not match:
            print("No matches in database. Run 'ingest' first.", file=sys.stderr)
            conn.close()
            return 1
    
    conn.close()
    
    # Generate output filename
    match_id = match['id']
    output_dir = args.output or "reports"
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"match_{match_id}_{match.get('map_name', 'unknown').replace(' ', '_')}.pdf"
    output_path = os.path.join(output_dir, filename)
    
    print(f"Generating PDF report for match #{match_id}...")
    generate_match_pdf(match, output_path, player_name=args.player)
    print(f"✅ PDF saved to: {output_path}")
    
    return 0


def cmd_pdf_stats(args):
    """Generate PDF stats report for a player."""
    from .pdf_stats import generate_stats_pdf
    
    output_dir = args.output or "reports"
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"stats_{args.player}.pdf"
    output_path = os.path.join(output_dir, filename)
    
    print(f"Generating stats PDF for {args.player}...")
    try:
        generate_stats_pdf(args.player, output_path, db_path=args.db)
        print(f"✅ PDF saved to: {output_path}")
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


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
    p_report.add_argument("--last", action="store_true", default=True, help="Show last match (default)")
    p_report.add_argument("--id", dest="match_id", type=int, help="Match ID")
    p_report.add_argument("--all", action="store_true", help="List all matches (requires --player)")
    p_report.add_argument("--player", "-p", default=None, help="Player perspective")
    p_report.add_argument("--limit", type=int, default=50, help="Limit number of matches in --all mode")
    
    # stats
    p_stats = subs.add_parser("stats", help="Player statistics")
    p_stats.add_argument("player", help="Player name")
    
    # patterns
    p_patterns = subs.add_parser("patterns", help="Generate and show pattern analysis")
    p_patterns.add_argument("--player", "-p", default="blzulian", help="Player name")
    
    # pdf
    p_pdf = subs.add_parser("pdf", help="Generate PDF report for a match")
    p_pdf.add_argument("match_id", type=int, nargs='?', help="Match ID (omit for latest match)")
    p_pdf.add_argument("--player", "-p", default=None, help="Player perspective")
    p_pdf.add_argument("--output", "-o", default="reports", help="Output directory (default: reports/)")
    
    # pdf-stats
    p_pdf_stats = subs.add_parser("pdf-stats", help="Generate PDF stats report for a player")
    p_pdf_stats.add_argument("player", help="Player name")
    p_pdf_stats.add_argument("--output", "-o", default="reports", help="Output directory (default: reports/)")
    
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
    elif args.command == "patterns":
        return cmd_patterns(args)
    elif args.command == "pdf":
        return cmd_pdf(args)
    elif args.command == "pdf-stats":
        return cmd_pdf_stats(args)


if __name__ == "__main__":
    sys.exit(main() or 0)
