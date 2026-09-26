"""Loading inputs: existing transcripts, course-material PDFs and online lectures."""

import json
import re
from collections import Counter
from pathlib import Path

MEDIA_EXTENSIONS = {
    ".mp4", ".mkv", ".mov", ".avi", ".webm", ".wmv", ".flv", ".m4v",
    ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".wma",
}
TRANSCRIPT_EXTENSIONS = {".txt", ".md", ".srt", ".vtt", ".json", ".docx", ".pdf"}

_SUB_TIMING = re.compile(r"^(\d{1,2}:)?\d{1,2}:\d{2}[.,]\d{3}\s*-->\s*.*$")


def clean_path(raw):
    """Strip the quotes Windows adds when a file is dragged into the console."""
    return raw.strip().strip('"').strip("'").strip()


def is_url(text):
    return bool(re.match(r"^https?://", text.strip(), re.I))


def load_transcript(path):
    """Read a transcript in any common format and return plain text."""
    path = Path(path)
    ext = path.suffix.lower()
    if ext == ".docx":
        import docx

        return "\n".join(p.text for p in docx.Document(path).paragraphs if p.text.strip())
    if ext == ".pdf":
        import fitz

        with fitz.open(path) as doc:
            return "\n".join(page.get_text() for page in doc)
    text = path.read_text(encoding="utf-8", errors="replace")
    if ext == ".json":
        data = json.loads(text)
        if isinstance(data, dict) and "segments" in data:
            return "\n".join(s.get("text", "").strip() for s in data["segments"])
        if isinstance(data, dict) and "text" in data:
            return data["text"]
        return text
    if ext in (".srt", ".vtt"):
        return _subtitles_to_text(text)
    return text


def _subtitles_to_text(text):
    """Turn SRT/VTT into '[mm:ss] line' text, dropping numbering and repeated cues."""
    out, stamp, last = [], None, None
    for line in text.splitlines():
        line = line.strip()
        if not line or line == "WEBVTT" or line.isdigit() or line.startswith(("NOTE", "Kind:", "Language:")):
            continue
        if _SUB_TIMING.match(line):
            start = line.split("-->")[0].strip().replace(",", ".")
            parts = start.split(".")[0].split(":")
            stamp = ":".join(parts[-2:]) if len(parts) == 3 and parts[0] in ("0", "00") else ":".join(parts)
            continue
        line = re.sub(r"<[^>]+>", "", line)
        if line and line != last:
            out.append(f"[{stamp}] {line}" if stamp else line)
            last = line
    return "\n".join(out)


class CourseMaterial:
    """A PDF of slides/handouts. Sent to Claude as a real PDF (so figures and
    diagrams are seen), with extracted text kept as a fallback."""

    def __init__(self, path):
        import fitz

        self.path = Path(path)
        self.data = self.path.read_bytes()
        with fitz.open(self.path) as doc:
            self.pages = len(doc)
            self.page_texts = [page.get_text() for page in doc]
        self.text = "\n\n".join(
            f"--- Page {i + 1} ---\n{t.strip()}" for i, t in enumerate(self.page_texts)
        )


def extract_glossary(materials, limit=60):
    """Pick distinctive terms from the course material (acronyms, capitalised and
    technical words, slide titles) to steer Whisper toward the right spellings."""
    counts = Counter()
    titles = []
    for mat in materials:
        for page in mat.page_texts:
            lines = [l.strip() for l in page.splitlines() if l.strip()]
            if lines and 3 <= len(lines[0]) <= 60:
                titles.append(lines[0])
            for term in re.findall(r"\b[A-Z]{2,}[a-z]?s?\b", page):  # acronyms
                counts[term] += 2
            for term in re.findall(r"\b[A-Z][a-z]+(?:[- ][A-Z][a-z]+)+\b", page):  # Multi Word Names
                counts[term] += 2
            for term in re.findall(r"\b[A-Za-z]+(?:-[A-Za-z]+)+\b", page):  # hyphenated-terms
                counts[term] += 1
            for term in re.findall(r"\b[a-zA-Z]{9,}\b", page):  # long technical words
                counts[term.lower()] += 1
    terms, seen = [], set()
    for term in titles + [t for t, c in counts.most_common() if c >= 2]:
        key = term.lower()
        if key not in seen:
            seen.add(key)
            terms.append(term)
        if len(terms) >= limit:
            break
    return terms


def download_audio(url, out_dir):
    """Download the audio track of an online lecture (YouTube and most video sites)."""
    import yt_dlp

    opts = {
        "format": "bestaudio/best",
        "outtmpl": str(Path(out_dir) / "lecture_audio.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info), info.get("title")
