#!/usr/bin/env python3
"""Test dual-bound housing detection implementation."""

import json
import glob
import zipfile
import os
import sys

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from agelytics.parser import parse_replay
from agelytics.pdf_scouting import generate_rich_scouting_pdf

def test_single_match():
    """Parse one match and print housing metrics."""
    print("=" * 60)
    print("TEST 1: Single Match Parse")
    print("=" * 60)
    
    replay_files = sorted(glob.glob('replays/*19012079*.aoe2record'))
    if not replay_files:
        print("❌ No replay files found!")
        return False
    
    zf = replay_files[-1]
    print(f"📂 Parsing: {os.path.basename(zf)}")
    
    with zipfile.ZipFile(zf) as z:
        inner = [n for n in z.namelist() if n.endswith('.aoe2record')]
        if not inner:
            print("❌ No .aoe2record file inside ZIP!")
            return False
        
        extracted = z.extract(inner[0], '/tmp/test_housing')
    
    data = parse_replay(extracted)
    
    if not data:
        print("❌ Parse returned None!")
        return False
    
    print("\n✅ Parse successful!")
    print("\n📊 Housing Metrics:")
    print(f"   housed_time_lower: {data.get('housed_time_lower')}")
    print(f"   housed_time_upper: {data.get('housed_time_upper')}")
    print(f"   tc_idle_effective_lower: {data.get('tc_idle_effective_lower')}")
    print(f"   tc_idle_effective_upper: {data.get('tc_idle_effective_upper')}")
    
    # Verify old fields are removed
    if 'housed_time' in data:
        print("⚠️  Warning: Old 'housed_time' field still present!")
    if 'tc_idle_effective' in data:
        print("⚠️  Warning: Old 'tc_idle_effective' field still present!")
    
    return True


def test_pdf_generation():
    """Generate PDF with all matches."""
    print("\n" + "=" * 60)
    print("TEST 2: PDF Generation with All Matches")
    print("=" * 60)
    
    replay_files = sorted(glob.glob('replays/*19012079*.aoe2record'))
    
    if len(replay_files) < 5:
        print(f"⚠️  Only {len(replay_files)} replays found. Need at least 5 for good testing.")
    
    stats = []
    for i, zf in enumerate(replay_files, 1):
        print(f"📂 Parsing {i}/{len(replay_files)}: {os.path.basename(zf)}")
        try:
            with zipfile.ZipFile(zf) as z:
                inner = [n for n in z.namelist() if n.endswith('.aoe2record')]
                if not inner:
                    continue
                extracted = z.extract(inner[0], '/tmp/test_housing_all')
            
            d = parse_replay(extracted)
            if d:
                stats.append(d)
        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue
    
    print(f"\n✅ Successfully parsed {len(stats)}/{len(replay_files)} matches")
    
    if not stats:
        print("❌ No valid stats collected!")
        return False
    
    output_path = '/tmp/urubu_scouting_housing.pdf'
    print(f"\n📄 Generating PDF: {output_path}")
    
    try:
        generate_rich_scouting_pdf(stats, 'Urubu', output_path, profile_id=19012079)
        print(f"✅ PDF generated successfully!")
        print(f"   File size: {os.path.getsize(output_path) / 1024:.1f} KB")
        return True
    except Exception as e:
        print(f"❌ PDF generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    
    success = True
    
    # Test 1: Single match parse
    if not test_single_match():
        success = False
    
    # Test 2: PDF generation
    if not test_pdf_generation():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
