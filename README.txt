RestoreMusic — Step by step
═══════════════════════════

STEP 1 — Copy your iTunes XML here
───────────────────────────────────
Put your "iTunes Music Library.xml" file in this folder:
  C:\Users\Paul\Documents\code\RestoreMusic\

STEP 2 — Split the XML
───────────────────────
Open Command Prompt, go to this folder and run:

  cd C:\Users\Paul\Documents\code\RestoreMusic
  python split_xml.py

This creates a "chunks" folder with files like:
  chunk_001.xml  (~30 MB)
  chunk_002.xml  (~30 MB)
  ...

STEP 3 — Extract song names from a chunk
─────────────────────────────────────────
Edit extract_links.py — change CHUNK_FILE to the chunk you want:
  CHUNK_FILE = "chunks/chunk_001.xml"

Then run:
  python extract_links.py

This creates "songs_list.txt" with lines like:
  Pink Floyd - Comfortably Numb  [The Wall]
  Radiohead - Karma Police  [OK Computer]

STEP 4 — Get links from Claude
────────────────────────────────
Open a chat with Claude, paste the contents of songs_list.txt and say:
  "For each song, give me the best YouTube or SoundCloud link to download it"

Claude will return a list of URLs.

STEP 5 — Download with Media Human
────────────────────────────────────
Copy the URLs into Media Human YouTube to MP3 Converter and download!

Repeat steps 3-5 for each chunk until all songs are recovered.
═══════════════════════════════════════════════════════════════
