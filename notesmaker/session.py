"""Live-lecture sessions that can be stopped and continued later.

Each session lives in its own output folder: a session.json with the lecture's settings,
one WAV file per recording sitting (lecture_recording_part1.wav, part2, ...) and the running
live transcript. Timestamps carry on from where the previous sitting stopped.
"""

import json
import re
import wave
from datetime import datetime
from pathlib import Path

SESSION_FILE = "session.json"
PART_PATTERN = re.compile(r"lecture_recording_part(\d+)\.wav$")

# Settings remembered between sittings.
SETTINGS = ("input", "pdf", "topic", "accent", "language", "notes_language", "quality",
            "refine", "transcript")


def save(out_dir, status, args, name):
    data = {k: getattr(args, k, None) for k in SETTINGS}
    data.update(status=status, name=name, updated=datetime.now().isoformat(timespec="seconds"))
    (Path(out_dir) / SESSION_FILE).write_text(json.dumps(data, indent=2), encoding="utf-8")


def load(out_dir):
    return json.loads((Path(out_dir) / SESSION_FILE).read_text(encoding="utf-8"))


def restore(args, out_dir):
    """Copy a saved session's settings onto args. Returns the lecture name."""
    data = load(out_dir)
    for key in SETTINGS:
        if data.get(key) is not None:
            setattr(args, key, data[key])
    return data.get("name") or Path(out_dir).name


def parts(out_dir):
    found = [(int(m.group(1)), p) for p in Path(out_dir).glob("lecture_recording_part*.wav")
             if (m := PART_PATTERN.search(p.name))]
    return [p for _, p in sorted(found)]


def next_part_path(out_dir):
    return Path(out_dir) / f"lecture_recording_part{len(parts(out_dir)) + 1}.wav"


def wav_seconds(path):
    try:
        with wave.open(str(path), "rb") as w:
            return w.getnframes() / w.getframerate()
    except (wave.Error, EOFError, OSError):
        return 0.0


def recorded_seconds(out_dir):
    return sum(wav_seconds(p) for p in parts(out_dir))


def find_unfinished(output_root):
    """Live sessions that were saved for later (or interrupted), newest first."""
    found = []
    for f in Path(output_root).glob(f"*/{SESSION_FILE}"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if data.get("status") != "finished":
            found.append((f.parent, data))
    return sorted(found, key=lambda item: item[1].get("updated", ""), reverse=True)
