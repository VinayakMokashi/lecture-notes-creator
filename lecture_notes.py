"""Lecture Notes Creator

Turns a lecture (video file, online link, live audio, or an existing transcript) plus the
lecture PDF into detailed study notes, saved as a PDF.

Run with no arguments for a guided set of questions, or see --help for options.
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from notesmaker import sources  # noqa: E402
from notesmaker.transcribe import fmt_ts  # noqa: E402

LIVE_MODEL = "small"  # fast enough to keep up in real time on a laptop CPU


def load_env_file():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"'))


def ensure_api_key(interactive):
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        return
    if not interactive:
        sys.exit(
            "No Anthropic API key found. Put ANTHROPIC_API_KEY=sk-ant-... in a file named .env "
            f"in {ROOT}, or set the ANTHROPIC_API_KEY environment variable."
        )
    print("\nAn Anthropic API key is needed to write the notes (get one at console.anthropic.com).")
    key = input("Paste your API key: ").strip()
    if not key:
        sys.exit("No API key given.")
    os.environ["ANTHROPIC_API_KEY"] = key
    (ROOT / ".env").write_text(f"ANTHROPIC_API_KEY={key}\n", encoding="utf-8")
    print("Saved to .env so you won't be asked again.")


# ---------------------------------------------------------------------------
# Guided mode
# ---------------------------------------------------------------------------

def ask(prompt, default=""):
    answer = input(f"{prompt}{f' [{default}]' if default else ''}: ").strip()
    return answer or default


def ask_path(prompt, must_exist=True, optional=False):
    while True:
        raw = sources.clean_path(input(f"{prompt}: "))
        if not raw and optional:
            return None
        if raw and (not must_exist or Path(raw).exists()):
            return raw
        print("  That file wasn't found - try dragging it into this window.")


def guided(args):
    print("=" * 60)
    print("  LECTURE NOTES CREATOR")
    print("=" * 60)
    print("Tip: you can drag files into this window instead of typing paths.\n")

    if not args.input and not args.transcript:
        print("What do you have?")
        print("  1) A video or audio file of the lecture")
        print("  2) A link to an online lecture (YouTube etc.)")
        print("  3) A lecture playing live on this computer (browser, Zoom, Teams...)")
        print("  4) A lecture happening in the room (record with the microphone)")
        print("  5) Only a transcript")
        choice = ask("Choose 1-5", "1")
        if choice == "1":
            args.input = ask_path("Video/audio file")
        elif choice == "2":
            args.input = ask("Lecture link")
        elif choice in ("3", "4"):
            args.input = "live" if choice == "3" else "mic"
            if offer_resume(args):
                return args
        else:
            args.transcript = ask_path("Transcript file (.txt, .srt, .vtt, .docx, .pdf)")

    if args.input and not args.transcript:
        args.transcript = ask_path(
            "Do you also have a transcript? Drag it here, or press Enter to skip",
            optional=True,
        )

    if not args.pdf:
        print("\nDrag in the lecture PDF(s) (slides, notes, handouts). Press Enter when done.")
        args.pdf = []
        while True:
            p = ask_path(f"  PDF {len(args.pdf) + 1} (Enter to finish)", optional=True)
            if not p:
                break
            args.pdf.append(p)

    if args.topic is None:
        args.topic = ask("\nCourse / lecture topic (optional, helps accuracy)") or None
    if args.accent is None:
        args.accent = ask("Lecturer's accent (e.g. Indian, British, Chinese - optional)") or None
    if args.language is None:
        args.language = ask("Language spoken (e.g. en, hi, fr - Enter to auto-detect)") or None
    return args


def offer_resume(args):
    """If there are live lectures saved for later, offer to continue one.
    Returns True if the user picked one (its settings are then loaded into args)."""
    from notesmaker import session

    args.resume = args.resume or False  # False = already asked
    unfinished = session.find_unfinished(args.out)[:5]
    if not unfinished:
        return False
    print("\nYou have unfinished live lectures:")
    print("  0) Start a new lecture")
    for i, (folder, data) in enumerate(unfinished, 1):
        recorded = fmt_ts(session.recorded_seconds(folder))
        when = data.get("updated", "")[:16].replace("T", " ")
        print(f"  {i}) Continue '{data.get('name') or folder.name}' "
              f"- {recorded} recorded, last on {when}")
    choice = ask("Choose", "0")
    if not choice.isdigit() or not 1 <= int(choice) <= len(unfinished):
        return False
    folder = unfinished[int(choice) - 1][0]
    session.restore(args, folder)
    args.resume = str(folder)
    return True


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def slugify(text):
    text = re.sub(r"[^\w\s-]", "", text).strip()
    return re.sub(r"[\s]+", "_", text)[:50] or "lecture"


def run(args, interactive):
    from notesmaker import session, transcribe

    if args.input in ("live", "mic") and args.resume is None and sys.stdin.isatty():
        offer_resume(args)
    if args.resume:
        if not (Path(args.resume) / session.SESSION_FILE).exists():
            sys.exit(f"No saved live lecture found in {args.resume}")
        session.restore(args, args.resume)

    whisper_model = transcribe.QUALITY_MODELS[args.quality]
    live = args.input in ("live", "mic")
    url = args.input and not live and sources.is_url(args.input)

    if args.input and not live and not url:
        args.input = sources.clean_path(args.input)
        ext = Path(args.input).suffix.lower()
        if ext in sources.TRANSCRIPT_EXTENSIONS and ext not in sources.MEDIA_EXTENSIONS:
            args.transcript, args.input = args.transcript or args.input, None
        elif not Path(args.input).exists():
            sys.exit(f"File not found: {args.input}")

    materials = []
    for p in args.pdf or []:
        p = sources.clean_path(p)
        print(f"Reading course material: {Path(p).name}")
        materials.append(sources.CourseMaterial(p))
    args.pdf = [str(m.path.resolve()) for m in materials]
    if args.transcript:
        args.transcript = str(Path(sources.clean_path(args.transcript)).resolve())
    glossary = sources.extract_glossary(materials)
    prompt = transcribe.build_initial_prompt(args.topic, glossary, args.accent)

    # Output folder
    if args.input and not live and not url:
        name = Path(args.input).stem
    elif args.transcript:
        name = Path(sources.clean_path(args.transcript)).stem
    elif materials:
        name = materials[0].path.stem
    else:
        name = args.topic or "lecture"
    if args.resume:
        out_dir = Path(args.resume)
        name = session.load(out_dir).get("name") or name
        print(f"Continuing '{name}' - {fmt_ts(session.recorded_seconds(out_dir))} "
              "recorded so far.")
    else:
        out_dir = Path(args.out) / f"{slugify(name)}_{datetime.now():%Y-%m-%d_%H%M}"
        out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output folder: {out_dir}\n")

    transcripts = []
    language = args.language

    if args.transcript:
        path = sources.clean_path(args.transcript)
        print(f"Using your transcript: {Path(path).name}")
        transcripts.append(("student-supplied transcript", sources.load_transcript(path)))

    if url:
        print("Downloading lecture audio...")
        media, title = sources.download_audio(args.input, out_dir)
        if title and not args.topic:
            args.topic = title
        text, language = transcribe.transcribe_file(media, whisper_model, language, prompt)
        transcripts.append(("automatic speech recognition", text))
    elif live:
        session.save(out_dir, "recording", args, name)
        live_txt = out_dir / "transcript_live.txt"
        _, detected = transcribe.live_transcribe(
            args.input, str(session.next_part_path(out_dir)), str(live_txt), LIVE_MODEL,
            language, prompt, start_offset=session.recorded_seconds(out_dir),
        )
        args.language = language = language or detected
        if not lecture_finished():
            session.save(out_dir, "paused", args, name)
            print(f"\nSaved ({fmt_ts(session.recorded_seconds(out_dir))} recorded so far). "
                  "To continue: run run.bat, choose option 3 (or 4), and pick this lecture.")
            return None
        session.save(out_dir, "finished", args, name)
        text = live_txt.read_text(encoding="utf-8") if live_txt.exists() else ""
        if args.refine:
            print(f"\nRe-transcribing the full recording with the more accurate '{whisper_model}' "
                  "model (use --no-refine to skip)...")
            texts, offset = [], 0.0
            for part in session.parts(out_dir):
                seconds = session.wav_seconds(part)
                if seconds >= 1:
                    part_text, language = transcribe.transcribe_file(
                        str(part), whisper_model, language, prompt, offset
                    )
                    texts.append(part_text)
                offset += seconds
            text = "\n".join(t for t in texts if t)
        transcripts.append(("automatic speech recognition", text))
    elif args.input:
        print(f"Transcribing {Path(args.input).name} with Whisper '{whisper_model}'...")
        text, language = transcribe.transcribe_file(args.input, whisper_model, language, prompt)
        transcripts.append(("automatic speech recognition", text))

    for label, text in transcripts:
        if label == "automatic speech recognition":
            (out_dir / "transcript.txt").write_text(text, encoding="utf-8")
            print(f"Transcript saved: {out_dir / 'transcript.txt'}")

    if not transcripts or not any(t.strip() for _, t in transcripts):
        sys.exit("No speech was captured or transcribed, so there is nothing to make notes from.")

    return make_notes(args, interactive, transcripts, materials, language, out_dir, name)


def lecture_finished():
    try:
        answer = ask("\nIs the lecture finished?  Y = make the notes now,  "
                     "L = save it and continue later", "Y")
    except EOFError:
        return True
    return not answer.lower().startswith("l")


def make_notes(args, interactive, transcripts, materials, language, out_dir, name):
    from notesmaker import notes

    engine = args.engine
    if engine == "auto":
        engine = "claude-code" if notes.find_claude_code() else "api"
    if engine == "api":
        ensure_api_key(interactive)
    info = {
        "Course / topic": args.topic,
        "Lecturer's accent": args.accent,
        "Language spoken": language,
        "Write the notes in": args.notes_language,
        "Course material": ", ".join(m.path.name for m in materials) if materials else None,
    }
    try:
        if engine == "claude-code":
            md = notes.generate_notes_claude_code(
                transcripts, materials, info, out_dir, args.claude_model
            )
        else:
            md = notes.generate_notes(transcripts, materials, info)
    except Exception as e:
        print(f"\nCould not generate the notes: {e}")
        if (out_dir / "transcript.txt").exists():
            print("Your transcript is saved - to retry without transcribing again, run:\n"
                  f'  run.bat --transcript "{out_dir / "transcript.txt"}" '
                  + " ".join(f'--pdf "{m.path}"' for m in materials))
        sys.exit(1)

    return write_outputs(md, out_dir, name)


def write_outputs(md, out_dir, name):
    from notesmaker import render

    title_match = re.search(r"^#\s+(.+)$", md, re.M)
    title = title_match.group(1).strip() if title_match else name
    md_path = out_dir / "notes.md"
    html_path = out_dir / "notes.html"
    short = slugify(title)
    if len(short) > 40:  # keep file paths short (Windows limits them to 260 characters)
        short = short[:40].rsplit("_", 1)[0]
    pdf_path = out_dir / f"{short}_notes.pdf"
    md_path.write_text(md, encoding="utf-8")
    html_path.write_text(
        render.markdown_to_html(md, title, f"Generated {datetime.now():%d %B %Y}"), encoding="utf-8"
    )
    print("Creating PDF...")
    try:
        render.html_to_pdf(html_path, pdf_path)
    except Exception as e:
        print(f"PDF step failed ({e}). The notes are in {md_path} and {html_path}.")
        return None
    print("\nDone!")
    print(f"  Notes (PDF):      {pdf_path}")
    print(f"  Notes (Markdown): {md_path}")
    if hasattr(os, "startfile"):
        os.startfile(pdf_path)
    return pdf_path


def main():
    load_env_file()
    parser = argparse.ArgumentParser(
        description="Create detailed study notes (PDF) from a lecture and its PDF.",
        epilog="Run with no arguments for guided mode. Examples:\n"
               '  run.bat "lecture.mp4" --pdf "slides.pdf"\n'
               '  run.bat https://youtu.be/xyz --pdf "slides.pdf" --accent Indian\n'
               '  run.bat live --pdf "slides.pdf"\n'
               '  run.bat --transcript "lecture.txt" --pdf "slides.pdf"',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", nargs="?",
                        help="video/audio file, a URL, 'live' (this computer's sound) or 'mic'")
    parser.add_argument("--transcript", help="an existing transcript (.txt/.srt/.vtt/.docx/.pdf)")
    parser.add_argument("--pdf", action="append", help="lecture PDF (repeat for several)")
    parser.add_argument("--topic", help="course or lecture topic")
    parser.add_argument("--accent", help="lecturer's accent, e.g. Indian, British, Nigerian")
    parser.add_argument("--language", help="spoken language code (en, hi, fr...); default: auto")
    parser.add_argument("--notes-language", default="English", help="language to write notes in")
    parser.add_argument("--quality", choices=["fast", "balanced", "best"], default="balanced",
                        help="transcription accuracy vs speed (default: balanced)")
    parser.add_argument("--no-refine", dest="refine", action="store_false",
                        help="live mode: skip the accurate second pass over the recording")
    parser.add_argument("--engine", choices=["auto", "claude-code", "api"], default="auto",
                        help="who writes the notes: claude-code = your Claude subscription via "
                             "Claude Code (free with a Pro/Max plan), api = Anthropic API key "
                             "(billed per use); auto = claude-code if installed (default)")
    parser.add_argument("--claude-model", default="opus",
                        help="model for the claude-code engine (default: opus)")
    parser.add_argument("--resume", metavar="FOLDER",
                        help="continue a live lecture that was saved for later")
    parser.add_argument("--render", metavar="NOTES_MD",
                        help="only re-create the PDF from an existing notes.md")
    parser.add_argument("--out", default=str(ROOT / "output"), help="output folder")
    args = parser.parse_args()

    if args.render:
        md_path = Path(sources.clean_path(args.render))
        write_outputs(md_path.read_text(encoding="utf-8"), md_path.parent, md_path.parent.name)
        return

    interactive = not args.input and not args.transcript and not args.resume
    if interactive or (args.input and not args.pdf and not args.resume and sys.stdin.isatty()):
        args = guided(args)
        interactive = True
    run(args, interactive)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled.")
