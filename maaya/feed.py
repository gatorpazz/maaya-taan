"""Podcast RSS for out/lessons so a phone podcast app can subscribe.
Serve the out/ folder (e.g. `python -m http.server -d out 8000`) or copy it to any static host."""
from __future__ import annotations

import datetime as dt
import subprocess
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape


def _duration(mp3: Path) -> int:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp3)], capture_output=True, text=True)
    return int(float(out.stdout.strip() or 0))


def write_feed(lessons_dir: Path, base_url: str, out: Path, title: str = "Maaya T'aan") -> Path:
    items = []
    for i, mp3 in enumerate(sorted(lessons_dir.glob("*.mp3"))):
        secs = _duration(mp3)
        pub = dt.datetime.fromtimestamp(mp3.stat().st_mtime, dt.timezone.utc)
        items.append(f"""
    <item>
      <title>{escape(mp3.stem)}</title>
      <enclosure url="{escape(base_url.rstrip('/'))}/lessons/{escape(mp3.name)}" length="{mp3.stat().st_size}" type="audio/mpeg"/>
      <guid isPermaLink="false">{escape(mp3.stem)}</guid>
      <pubDate>{format_datetime(pub)}</pubDate>
      <itunes:duration>{secs // 60}:{secs % 60:02d}</itunes:duration>
      <itunes:episode>{i + 1}</itunes:episode>
    </item>""")
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>{escape(title)}</title>
    <link>{escape(base_url)}</link>
    <language>en</language>
    <description>Pimsleur-style Yucatec Maya lessons, generated locally.</description>
    <itunes:type>serial</itunes:type>{''.join(items)}
  </channel>
</rss>
"""
    out.write_text(xml, encoding="utf-8")
    return out
