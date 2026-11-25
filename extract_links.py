"""
extract_links.py
────────────────
Reads a chunk XML file produced by split_xml.py,
prints every track as:   Artist - Song Title
so you can paste the list into a chat with Claude
and ask for YouTube / Bandcamp / SoundCloud links.
"""
import xml.etree.ElementTree as ET
import sys
import os

# ─── CONFIG ───────────────────────────────────────────────────────────────────
CHUNK_FILE = "chunks/chunk_001.xml"   # <-- change to the chunk you want
OUTPUT_TXT = "songs_list.txt"
# ──────────────────────────────────────────────────────────────────────────────

def get_track_value(track_dict, key_name):
    children = list(track_dict)
    for i, child in enumerate(children):
        if child.tag == "key" and child.text == key_name:
            return children[i + 1].text if i + 1 < len(children) else None
    return None

def extract(chunk_file, output_txt):
    if not os.path.exists(chunk_file):
        print(f"ERROR: File not found -> {chunk_file}")
        sys.exit(1)

    tree = ET.parse(chunk_file)
    root = tree.getroot()

    # Navigate to the Tracks dict
    top_dict = root.find("dict")
    children = list(top_dict)
    tracks_dict = None
    for i, child in enumerate(children):
        if child.tag == "key" and child.text == "Tracks":
            tracks_dict = children[i + 1]
            break

    if tracks_dict is None:
        print("ERROR: No Tracks section found.")
        sys.exit(1)

    track_children = list(tracks_dict)
    pairs = [(track_children[i+1]) for i in range(0, len(track_children)-1, 2)]

    songs = []
    for track_dict in pairs:
        artist = get_track_value(track_dict, "Artist") or "Unknown Artist"
        name   = get_track_value(track_dict, "Name")   or "Unknown Title"
        album  = get_track_value(track_dict, "Album")  or ""
        songs.append((artist, name, album))

    with open(output_txt, "w", encoding="utf-8") as f:
        for artist, name, album in songs:
            line = f"{artist} - {name}"
            if album:
                line += f"  [{album}]"
            f.write(line + "\n")

    print(f"Extracted {len(songs)} songs -> {output_txt}")
    print(f"Open {output_txt} and paste the contents into your Claude chat.")

if __name__ == "__main__":
    extract(CHUNK_FILE, OUTPUT_TXT)
