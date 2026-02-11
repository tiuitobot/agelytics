"""Download AoE2 DE replay files from Microsoft servers."""

import httpx
import os
import time
import logging
from pathlib import Path
from typing import Optional

from . import api_client

REPLAY_URL = "https://aoe.ms/replay/"
DEFAULT_DOWNLOAD_DIR = "replays"
TIMEOUT = 30.0

logger = logging.getLogger(__name__)


def download_replay(
    match_id: int,
    profile_id: int,
    output_dir: str = DEFAULT_DOWNLOAD_DIR,
    filename: str = None,
) -> Optional[Path]:
    """Download a single replay file.

    Args:
        match_id: The game/match ID from aoe2companion API
        profile_id: The profile ID (determines point of view)
        output_dir: Directory to save replays (created if doesn't exist)
        filename: Custom filename. Default: {match_id}_{profile_id}.aoe2record

    Returns:
        Path to downloaded file, or None if download failed (404, timeout, etc.)
    """
    # Create output directory if needed
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Determine filename
    if filename is None:
        filename = f"{match_id}_{profile_id}.aoe2record"
    file_path = output_path / filename

    # Skip if already exists
    if file_path.exists():
        logger.info(f"Replay already exists, skipping: {file_path}")
        return file_path

    # Build URL
    url = f"{REPLAY_URL}?gameId={match_id}&profileId={profile_id}"

    max_retries = 3
    for attempt in range(max_retries):
        try:
            with httpx.Client(timeout=TIMEOUT, follow_redirects=True) as client:
                response = client.get(url)
                response.raise_for_status()

                # Save to file
                with open(file_path, "wb") as f:
                    f.write(response.content)

                file_size_kb = len(response.content) / 1024
                logger.info(
                    f"Downloaded replay {match_id} ({file_size_kb:.1f} KB): {file_path}"
                )
                return file_path

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(
                    f"Replay not available (404) for match {match_id}, profile {profile_id}"
                )
                return None  # No retry for 404
            elif e.response.status_code == 429:
                wait = (attempt + 1) * 5  # 5s, 10s, 15s backoff
                logger.warning(
                    f"Rate limited (429) for match {match_id} — waiting {wait}s (attempt {attempt+1}/{max_retries})"
                )
                time.sleep(wait)
                continue
            else:
                logger.error(
                    f"HTTP error {e.response.status_code} downloading match {match_id}: {e}"
                )
                return None

        except httpx.TimeoutException:
            logger.error(f"Timeout downloading match {match_id}")
            return None

        except Exception as e:
            logger.error(f"Error downloading match {match_id}: {e}")
            return None

    logger.error(f"Failed to download match {match_id} after {max_retries} retries")
    return None


def download_opponent_replays(
    opponent_profile_id: int, count: int = 20, output_dir: str = DEFAULT_DOWNLOAD_DIR,
    only_1v1: bool = False, delay: float = 2.0
) -> list[Path]:
    """Download recent replays for an opponent (for scouting).

    Uses api_client.get_match_history() to get match IDs, then downloads each.
    By default downloads ALL ranked matches (1v1 + team). Use only_1v1=True to filter.
    Skips matches already downloaded.

    Args:
        opponent_profile_id: The opponent's profile ID
        count: Number of recent matches to attempt (default 20)
        output_dir: Where to save
        only_1v1: If True, only download 1v1 RM games
        delay: Seconds between downloads (default 2.0 — MS rate limits at ~0.5s)

    Returns:
        List of successfully downloaded file paths
    """
    logger.info(
        f"Fetching match history for opponent {opponent_profile_id} (count={count})..."
    )

    # Fetch match history
    matches = api_client.get_match_history(opponent_profile_id, count)
    if not matches:
        logger.warning(f"No match history found for profile {opponent_profile_id}")
        return []

    # Filter if requested
    if only_1v1:
        target_matches = [m for m in matches if m.get("matchtype_id") == 6]
    else:
        # All ranked matches (exclude unranked/custom)
        target_matches = [m for m in matches if m.get("matchtype_id") in (6, 7, 8, 9)]
    logger.info(
        f"Found {len(target_matches)} ranked matches out of {len(matches)} total"
    )

    # Download each
    successful_downloads = []
    for i, match in enumerate(target_matches, 1):
        match_id = match.get("match_id")
        if not match_id:
            continue

        logger.info(f"[{i}/{len(target_matches)}] Downloading match {match_id} ({match.get('map', '?')})...")

        file_path = download_replay(match_id, opponent_profile_id, output_dir)
        if file_path:
            successful_downloads.append(file_path)

        # Respect MS rate limits (429 at ~0.5s intervals)
        if i < len(target_matches):
            time.sleep(delay)

    logger.info(
        f"Downloaded {len(successful_downloads)}/{len(target_matches)} replays for opponent {opponent_profile_id}"
    )
    return successful_downloads


def batch_download(
    match_ids: list[tuple[int, int]],
    output_dir: str = DEFAULT_DOWNLOAD_DIR,
    max_concurrent: int = 3,
) -> list[Path]:
    """Download multiple replays. Each item is (match_id, profile_id).

    Sequential with small delay (0.5s) to be respectful to MS servers.
    Not truly concurrent — just a convenience wrapper.

    Args:
        match_ids: List of (match_id, profile_id) tuples
        output_dir: Directory to save replays
        max_concurrent: Not used (for future async implementation)

    Returns:
        List of successfully downloaded file paths
    """
    successful_downloads = []

    for i, (match_id, profile_id) in enumerate(match_ids, 1):
        logger.info(f"[{i}/{len(match_ids)}] Downloading match {match_id}...")

        file_path = download_replay(match_id, profile_id, output_dir)
        if file_path:
            successful_downloads.append(file_path)

        # Respect MS rate limits
        if i < len(match_ids):
            time.sleep(2.0)

    logger.info(
        f"Batch download complete: {len(successful_downloads)}/{len(match_ids)} successful"
    )
    return successful_downloads


if __name__ == "__main__":
    import sys

    # Configure logging for CLI usage
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s: %(message)s"
    )

    if len(sys.argv) < 2:
        print("Usage: python3 -m agelytics.replay_downloader <opponent_profile_id> [count]")
        sys.exit(1)

    profile_id = int(sys.argv[1])
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 20

    paths = download_opponent_replays(profile_id, count)
    print(f"\nDownloaded {len(paths)} replays")
