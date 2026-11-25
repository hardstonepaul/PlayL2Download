# PlayL2Download

Download play list of music.

Tools for rebuilding a music collection from an iTunes library export
(`iTunes Music Library.xml` / `Library.xml`): find out which tracks are no
longer on disk, list them by priority, and get them back.

## Files

| File | What it does |
|---|---|
| `find_missing.py` | Compares the library XML with the audio files still on disk and lists what is missing, most-loved first |
| `split_xml.py` | Splits a large library XML into ~30 MB chunks |
| `extract_links.py` | Turns one chunk into a plain `Artist - Title  [Album]` list |

The library XML and everything in `output/` and `chunks/` are personal data
and are ignored by git. Do not commit them.

## Setup

Copy your iTunes XML file into this folder:

```
C:\Users\Paul\Documents\code\RestoreMusic\
```

Python 3 is required. No extra packages are needed.

## Option A — List what is missing (recommended)

```
cd C:\Users\Paul\Documents\code\RestoreMusic
python find_missing.py
```

By default it reads `Library.xml` and scans `C:\Users\<you>\Music`. To use
other locations:

```
python find_missing.py --library "iTunes Music Library.xml" --music-dir "D:\Music"
```

It creates an `output` folder with:

- `missing_tracks.csv` — one row per missing track, sorted by rating, then play count
- `missing_albums.csv` — the same tracks grouped by album, sorted by priority
- `summary.txt` — the totals

A track counts as "on disk" only when a file with the same name and the same
size exists. Tracks with a similarly named file of a different size stay in
the missing list, with the file shown in the `Note` column.

## Option B — Step by step by chunks (original workflow)

### Step 1 — Copy your iTunes XML here

Put your `iTunes Music Library.xml` file in this folder. If your file has a
different name (for example `Library.xml`), edit `INPUT_FILE` at the top of
`split_xml.py`.

### Step 2 — Split the XML

Open Command Prompt, go to this folder and run:

```
cd C:\Users\Paul\Documents\code\RestoreMusic
python split_xml.py
```

This creates a `chunks` folder with files like:

```
chunk_001.xml  (~30 MB)
chunk_002.xml  (~30 MB)
...
```

### Step 3 — Extract song names from a chunk

Edit `extract_links.py` and change `CHUNK_FILE` to the chunk you want:

```python
CHUNK_FILE = "chunks/chunk_001.xml"
```

Then run:

```
python extract_links.py
```

This creates `songs_list.txt` with lines like:

```
Pink Floyd - Comfortably Numb  [The Wall]
Radiohead - Karma Police  [OK Computer]
```

### Step 4 — Get links from Claude

Open a chat with Claude, paste the contents of `songs_list.txt` and say:

> For each song, give me the best YouTube or SoundCloud link to download it

Claude will return a list of URLs.

### Step 5 — Download with MediaHuman

Copy the URLs into MediaHuman YouTube to MP3 Converter and download.

Repeat steps 3–5 for each chunk until all songs are recovered.
