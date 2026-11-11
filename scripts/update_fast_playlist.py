#!/usr/bin/env python3
"""Build one FAST M3U from BuddyChewChew/app-m3u-generator."""
from pathlib import Path
import re
import requests

BASE = "https://raw.githubusercontent.com/BuddyChewChew/app-m3u-generator/main/playlists"
SOURCES = [
    ("Pluto TV", "plutotv_all.m3u"),
    ("Samsung TV Plus", "samsungtvplus_all.m3u"),
    ("Plex TV", "plex_au.m3u"),
    ("Plex TV", "plex_ca.m3u"),
    ("Plex TV", "plex_es.m3u"),
    ("Plex TV", "plex_fr.m3u"),
    ("Plex TV", "plex_gb.m3u"),
    ("Plex TV", "plex_mx.m3u"),
    ("Plex TV", "plex_nz.m3u"),
    ("Plex TV", "plex_us.m3u"),
    ("Roku Channel", "roku_all.m3u"),
    ("Tubi", "tubi_all.m3u"),
]

session = requests.Session()
session.headers.update({"User-Agent": "My-IPTV-FAST-Playlist-Updater/1.0"})
headers = []
entries = []
seen = set()

for service, filename in SOURCES:
    url = f"{BASE}/{filename}"
    response = session.get(url, timeout=90)
    response.raise_for_status()
    content = response.text.lstrip("\ufeff")
    lines = content.splitlines()
    if not lines or not lines[0].startswith("#EXTM3U"):
        raise RuntimeError(f"Resposta M3U inválida: {filename}")

    header = lines[0]
    epg = re.findall(r'''(?:url-tvg|x-tvg-url)="([^"]+)"''', header, re.I)
    headers.extend(epg)

    current = []
    for line in lines[1:]:
        if line.startswith("#EXTINF:"):
            if current:
                entries.append((service, current))
            current = [line]
        elif current:
            current.append(line)
    if current:
        entries.append((service, current))

# Remove duplicate channel blocks while retaining the first occurrence.
output = ["#EXTM3U"]
if headers:
    unique_epg = list(dict.fromkeys(headers))
    output[0] += ' url-tvg="' + ",".join(unique_epg) + '"'

for service, block in entries:
    extinf = block[0]
    match = re.search(r'group-title="([^"]*)"', extinf, re.I)
    old_group = match.group(1) if match else "Outros"
    new_group = f"{service} | {old_group}"
    if match:
        extinf = extinf[:match.start(1)] + new_group + extinf[match.end(1):]
    else:
        comma = extinf.find(",")
        if comma == -1:
            continue
        extinf = extinf[:comma] + f' group-title="{new_group}"' + extinf[comma:]

    block[0] = extinf
    key = (service, extinf, tuple(line for line in block[1:] if line and not line.startswith("#")))
    if key in seen:
        continue
    seen.add(key)
    output.extend(block)

Path("fast_streaming_unificada.m3u").write_text("\n".join(output) + "\n", encoding="utf-8")
print(f"Playlist atualizada: {len(seen)} canais/blocos.")
