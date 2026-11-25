import xml.etree.ElementTree as ET
import os
import copy
import sys

# ─── CONFIG ───────────────────────────────────────────────────────────────────
INPUT_FILE  = "iTunes Music Library.xml"   # <-- change to your XML filename
OUTPUT_DIR  = "chunks"
MAX_MB      = 30
# ──────────────────────────────────────────────────────────────────────────────

MAX_BYTES = MAX_MB * 1024 * 1024

def log(msg):
    print(msg, flush=True)

def find_tracks_dict(root):
    """
    iTunes XML structure:
      <plist>
        <dict>
          <key>Tracks</key>
          <dict>   <-- this dict holds all track entries
            <key>123</key><dict>...</dict>
            ...
          </dict>
        </dict>
      </plist>
    Returns the <dict> element that contains all tracks.
    """
    top_dict = root.find("dict")
    if top_dict is None:
        log("ERROR: Could not find top-level <dict> in plist.")
        sys.exit(1)

    children = list(top_dict)
    for i, child in enumerate(children):
        if child.tag == "key" and child.text == "Tracks":
            return children[i + 1]   # the <dict> right after <key>Tracks</key>

    log("ERROR: Could not find <key>Tracks</key> in the XML.")
    sys.exit(1)

def write_chunk(track_pairs, chunk_index, output_dir):
    """
    Write a minimal valid iTunes-style plist containing only the given tracks.
    Each item in track_pairs is (key_element, dict_element).
    """
    plist_open  = '<?xml version="1.0" encoding="UTF-8"?>\n'
    plist_open += '<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" '
    plist_open += '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
    plist_open += '<plist version="1.0"><dict>'
    plist_open += '<key>Tracks</key><dict>'
    plist_close = '</dict></dict></plist>'

    filename = os.path.join(output_dir, f"chunk_{chunk_index:03d}.xml")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(plist_open)
        for key_el, dict_el in track_pairs:
            f.write(ET.tostring(key_el,  encoding="unicode"))
            f.write(ET.tostring(dict_el, encoding="unicode"))
        f.write(plist_close)

    size_mb = os.path.getsize(filename) / (1024 * 1024)
    log(f"  Wrote {filename}  ({len(track_pairs)} tracks, {size_mb:.1f} MB)")

def split(input_file, output_dir, max_bytes):
    if not os.path.exists(input_file):
        log(f"ERROR: File not found -> {input_file}")
        log("Make sure this script is in the same folder as your XML file,")
        log("or edit INPUT_FILE at the top of the script.")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    log(f"Parsing {input_file} ...")

    tree = ET.parse(input_file)
    root = tree.getroot()

    tracks_dict = find_tracks_dict(root)
    children = list(tracks_dict)

    # Children alternate: <key>id</key>  <dict>track info</dict>
    if len(children) % 2 != 0:
        log("WARNING: Odd number of children in Tracks dict — XML may be malformed.")

    pairs = [(children[i], children[i+1]) for i in range(0, len(children)-1, 2)]
    log(f"Found {len(pairs)} tracks total.")

    chunk_index   = 1
    current_pairs = []
    current_bytes = 0
    overhead      = len('<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd"><plist version="1.0"><dict><key>Tracks</key><dict></dict></dict></plist>'.encode())

    log(f"Splitting into {MAX_MB} MB chunks -> folder: {output_dir}/")

    for key_el, dict_el in pairs:
        entry_bytes = (len(ET.tostring(key_el,  encoding="unicode").encode("utf-8")) +
                       len(ET.tostring(dict_el, encoding="unicode").encode("utf-8")))

        if current_bytes + entry_bytes + overhead > max_bytes and current_pairs:
            write_chunk(current_pairs, chunk_index, output_dir)
            chunk_index   += 1
            current_pairs  = []
            current_bytes  = 0

        current_pairs.append((key_el, dict_el))
        current_bytes += entry_bytes

    if current_pairs:
        write_chunk(current_pairs, chunk_index, output_dir)

    log(f"\nDone! {chunk_index} chunk(s) saved to '{output_dir}' folder.")
    log("Send each chunk to Claude to extract song links.")

if __name__ == "__main__":
    split(INPUT_FILE, OUTPUT_DIR, MAX_BYTES)
