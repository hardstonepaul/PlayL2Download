"""
find_missing.py
───────────────
Compares an iTunes library export (Library.xml) with the audio files that
still exist on disk and writes what is missing, most-loved first.

Outputs (in ./output, ignored by git):
  missing_tracks.csv   one row per missing track, sorted by rating / plays
  missing_albums.csv   the same tracks grouped by album, sorted by priority
  summary.txt          the totals

Usage:
  python find_missing.py
  python find_missing.py --library Library.xml --music-dir "C:\\Users\\Paul\\Music"
"""
import argparse
import csv
import os
import plistlib
import re
import sys
import unicodedata
from collections import defaultdict
from urllib.parse import unquote, urlparse

AUDIO_EXT = {".mp3", ".m4a", ".m4p", ".aac", ".flac", ".wav", ".wma", ".ogg", ".aiff", ".aif"}


def norm(text):
    """Lowercase, strip accents and punctuation so names compare loosely."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def index_music_dir(music_dir):
    """Walk the music folder once and index every audio file."""
    by_name_size = set()
    by_size = defaultdict(list)
    by_name = defaultdict(list)
    names_norm = []
    count = 0
    for root, _dirs, files in os.walk(music_dir):
        for fname in files:
            stem, ext = os.path.splitext(fname)
            if ext.lower() not in AUDIO_EXT:
                continue
            path = os.path.join(root, fname)
            try:
                size = os.path.getsize(path)
            except OSError:
                continue
            count += 1
            by_name_size.add((fname.lower(), size))
            by_size[size].append(path)
            by_name[fname.lower()].append(path)
            names_norm.append((norm(stem), path))
    return count, by_name_size, by_size, by_name, names_norm


def location_basename(location):
    if not location:
        return ""
    return os.path.basename(unquote(urlparse(location).path))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--library", default="Library.xml")
    ap.add_argument("--music-dir", default=os.path.join(os.path.expanduser("~"), "Music"))
    ap.add_argument("--out-dir", default="output")
    args = ap.parse_args()

    if not os.path.exists(args.library):
        sys.exit(f"ERROR: library file not found -> {args.library}")
    if not os.path.isdir(args.music_dir):
        sys.exit(f"ERROR: music folder not found -> {args.music_dir}")

    print(f"Indexing {args.music_dir} ...", flush=True)
    n_files, by_name_size, by_size, by_name, names_norm = index_music_dir(args.music_dir)
    print(f"  {n_files} audio files on disk", flush=True)

    # "artist title" style lookup built from on-disk file names
    disk_words = defaultdict(list)
    for stem_norm, path in names_norm:
        disk_words[stem_norm].append(path)

    print(f"Reading {args.library} (this takes a minute) ...", flush=True)
    with open(args.library, "rb") as f:
        tracks = plistlib.load(f)["Tracks"]
    print(f"  {len(tracks)} tracks in library", flush=True)

    counts = defaultdict(int)
    missing = []
    for t in tracks.values():
        if t.get("Track Type") != "File":
            counts["skipped (stream/URL)"] += 1
            continue
        kind = t.get("Kind", "")
        if "video" in kind.lower() or "movie" in kind.lower():
            counts["skipped (video)"] += 1
            continue

        fname = location_basename(t.get("Location")).lower()
        size = t.get("Size")
        artist = t.get("Artist") or t.get("Album Artist") or ""
        name = t.get("Name") or ""

        # Only an identical file name AND byte size counts as "have".
        # Size alone collides too often across 100k+ files, and a matching
        # name with a different size is usually another rip of the song,
        # so those stay in the missing list with a note instead.
        if (fname, size) in by_name_size:
            counts["have: same file name and size"] += 1
            continue

        note = ""
        a, n = norm(artist), norm(name)
        if fname in by_name:
            note = "same file name on disk, different size: " + by_name[fname][0]
            counts["missing, but a similar file is on disk"] += 1
        elif a and n and (f"{a} {n}" in disk_words or f"{n} {a}" in disk_words):
            hit = disk_words.get(f"{a} {n}") or disk_words.get(f"{n} {a}")
            note = "artist + title match a file on disk: " + hit[0]
            counts["missing, but a similar file is on disk"] += 1
        else:
            counts["missing"] += 1

        missing.append({
            "Rating": (t.get("Rating") or 0) // 20 if not t.get("Rating Computed") else 0,
            "Plays": t.get("Play Count") or 0,
            "Artist": artist,
            "Title": name,
            "Album": t.get("Album") or "",
            "Album Artist": t.get("Album Artist") or artist,
            "Year": t.get("Year") or "",
            "Track": t.get("Track Number") or "",
            "Genre": t.get("Genre") or "",
            "Minutes": round((t.get("Total Time") or 0) / 60000, 1),
            "Bit Rate": t.get("Bit Rate") or "",
            "Last Played": str(t.get("Play Date UTC") or "")[:10],
            "Original Path": unquote(urlparse(t.get("Location") or "").path).lstrip("/"),
            "Note": note,
        })

    missing.sort(key=lambda r: (-r["Rating"], -r["Plays"], r["Artist"].lower(), r["Album"].lower(), r["Track"] or 0))

    os.makedirs(args.out_dir, exist_ok=True)
    tracks_csv = os.path.join(args.out_dir, "missing_tracks.csv")
    with open(tracks_csv, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(missing[0].keys()) if missing else ["Artist"])
        w.writeheader()
        w.writerows(missing)

    # Group by album
    albums = defaultdict(lambda: {"tracks": 0, "plays": 0, "rated": 0, "rating_sum": 0, "top": 0, "year": "", "genre": ""})
    for r in missing:
        a = albums[(r["Album Artist"], r["Album"])]
        a["tracks"] += 1
        a["plays"] += r["Plays"]
        if r["Rating"]:
            a["rated"] += 1
            a["rating_sum"] += r["Rating"]
            a["top"] = max(a["top"], r["Rating"])
        a["year"] = a["year"] or r["Year"]
        a["genre"] = a["genre"] or r["Genre"]

    album_rows = []
    for (artist, album), a in albums.items():
        album_rows.append({
            "Album Artist": artist,
            "Album": album or "(no album)",
            "Year": a["year"],
            "Genre": a["genre"],
            "Missing Tracks": a["tracks"],
            "Total Plays": a["plays"],
            "Top Rating": a["top"],
            "Avg Rating (rated tracks)": round(a["rating_sum"] / a["rated"], 1) if a["rated"] else "",
            "Rated Tracks": a["rated"],
        })
    album_rows.sort(key=lambda r: (-r["Top Rating"], -r["Total Plays"], r["Album Artist"].lower()))
    albums_csv = os.path.join(args.out_dir, "missing_albums.csv")
    with open(albums_csv, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(album_rows[0].keys()) if album_rows else ["Album"])
        w.writeheader()
        w.writerows(album_rows)

    lines = [f"Library tracks: {len(tracks)}", f"Audio files on disk: {n_files}", ""]
    for k in sorted(counts):
        lines.append(f"{counts[k]:>8}  {k}")
    lines += ["", "Missing tracks by rating:"]
    by_rating = defaultdict(int)
    for r in missing:
        by_rating[r["Rating"]] += 1
    for stars in sorted(by_rating, reverse=True):
        lines.append(f"{by_rating[stars]:>8}  {stars} stars" if stars else f"{by_rating[stars]:>8}  unrated")
    lines += ["", "Missing tracks by play count:"]
    for label, lo, hi in [("never played", 0, 0), ("1-4 plays", 1, 4), ("5-19 plays", 5, 19), ("20+ plays", 20, 10**9)]:
        lines.append(f"{sum(1 for r in missing if lo <= r['Plays'] <= hi):>8}  {label}")
    lines += ["", f"Missing albums: {len(album_rows)}"]
    summary = "\n".join(lines)
    with open(os.path.join(args.out_dir, "summary.txt"), "w", encoding="utf-8") as f:
        f.write(summary + "\n")

    print("\n" + summary)
    print(f"\nWrote {tracks_csv}\nWrote {albums_csv}")


if __name__ == "__main__":
    main()
