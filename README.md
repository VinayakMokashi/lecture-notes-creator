# Lecture Notes Creator

Turns a lecture and its slides/handout PDF into detailed, exam-ready study notes, saved as a PDF.

**New here? Follow the step-by-step guide: [HOW_TO_USE.md](HOW_TO_USE.md)**

It works with whatever you have:

| You have | What it does |
|---|---|
| A video or audio file | Transcribes it with Whisper (runs on your computer) |
| A link (YouTube, most video sites) | Downloads the audio, then transcribes it |
| A lecture playing live on this PC (browser, Zoom, Teams) | Records the computer's sound and transcribes as it plays |
| A lecture in the room | Records the microphone and transcribes as it goes |
| A transcript (.txt, .srt, .vtt, .docx, .pdf) | Uses it directly, fixing obvious recognition errors |
| A transcript **and** the video | Uses both and cross-checks them |

Claude then reads the transcript together with the lecture PDF (including its diagrams) and writes
structured notes: explanations, examples, formulas in proper math notation, what the lecturer
emphasised, and at the end Key Takeaways, Definitions, Formulas, Exam Questions, and a list of
anything that was unclear or contradictory.

## One-time setup

1. Install [Python 3.10+](https://www.python.org/downloads/) (tick "Add Python to PATH").
2. Double-click **`setup.bat`**.
3. Install [Claude Code](https://claude.com/claude-code) and log in with your Claude Pro or Max
   account (run `claude` once and follow the login).

That's it: **no API key, no per-lecture cost**. The notes are written by Claude through your
existing subscription (they count toward its normal usage limits). Transcription runs entirely on
your own computer, so it is free too.

You also need Microsoft Edge or Google Chrome (Edge comes with Windows); it is used to create the PDF.

<details>
<summary>Using an Anthropic API key instead (optional, billed per use)</summary>

Add `--engine api` to the command. The first time, the tool asks for the key and saves it in a
`.env` file (never uploaded to GitHub). If Claude Code isn't installed, the tool uses this
automatically.
</details>

## Making notes

Double-click **`run.bat`** and answer the questions:

1. What you have (file / link / live / microphone / transcript)
2. The file or link (drag files into the window instead of typing paths)
3. The lecture PDF(s): drag in as many as you like, press Enter when done
4. Topic, the lecturer's accent, and the language: all optional, but they improve accuracy

The finished PDF opens automatically. Everything is saved in `output\<lecture name>_<date>\`:
`..._notes.pdf`, `notes.md`, `transcript.txt` and, for live mode, the recordings (`lecture_recording_part1.wav`, ...).

**Shortcut:** drag a video file straight onto `run.bat`.

### Live lectures

> **Tip:** if the lecture is a recording with a link (YouTube, a course site), use option 2
> instead. It downloads the audio, so you don't need to keep it playing and can take breaks freely.
> Live mode is for lectures you can't download, or ones streamed in real time.

Choose option 3, wait for `>>> Recording <<<`, then play the lecture. The transcript appears as it
goes. Keep the PC's volume up: it records what the speakers play.

| Key | What it does |
|---|---|
| **P** | Pause for a break (pause the video too). Nothing is recorded and the timestamps stop, so you can use the PC freely. Press **P** again to resume, then press play. |
| **Enter** | Stop. You're asked whether the lecture is finished: **Y** writes the notes now, **L** saves it to continue later. |

**Continuing another day:** run `run.bat` and choose option 3 (or 4). It lists your unfinished
lectures; pick one and carry on. Your PDFs and settings are remembered, and the timestamps
continue where they stopped. When you finally answer **Y**, the notes cover every sitting.

When the lecture is finished, the full recording is re-transcribed with the more accurate model
before the notes are written.

## How long it takes

On a typical laptop without a graphics card, transcription takes about 35 minutes per hour of
lecture on the default setting. The first run also downloads the speech model (about 1.6 GB).
Writing the notes takes a few minutes.

## Command-line options (optional)

```
run.bat "lecture.mp4" --pdf "slides.pdf" --accent Indian --topic "Thermodynamics"
run.bat https://youtu.be/abc123 --pdf "slides.pdf"
run.bat live --pdf "slides.pdf"
run.bat --transcript "lecture.srt" --pdf "slides.pdf" --pdf "handout.pdf"
```

| Option | Meaning |
|---|---|
| `--quality fast / balanced / best` | Transcription speed vs accuracy (default `balanced`; `best` is about 3x slower) |
| `--language hi` | Spoken language, if auto-detection gets it wrong |
| `--notes-language Hindi` | Language to write the notes in (default English) |
| `--no-refine` | Live mode: skip the second, more accurate pass |
| `--resume output\<folder>` | Continue a live lecture saved for later (same as picking it from the menu) |
| `--engine claude-code / api` | Who writes the notes: your subscription via Claude Code (default) or an API key |
| `--claude-model sonnet` | Model used through Claude Code (default `opus`) |
| `--render output\...\notes.md` | Re-create the PDF after editing `notes.md` |

If writing the notes fails (for example, no internet, or you've hit your plan's usage limit), the
transcript is already saved and the tool prints the command to retry without transcribing again.
