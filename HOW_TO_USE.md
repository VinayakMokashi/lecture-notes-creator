# How to Use Lecture Notes Creator

Lecture Notes Creator turns a lecture into a PDF of detailed study notes. You give it the lecture
(a video, a link, a lecture playing on your computer, or a transcript) and the lecture's slides or
handout as a PDF. You get back notes with explanations, examples, formulas, the points the
lecturer stressed, and exam-style review questions.

It costs nothing extra. The lecture is transcribed on your own computer, and the notes are written
by Claude through your Claude Pro or Max subscription.

**Contents**

1. [One-time setup](#1-one-time-setup)
2. [Making notes: the short version](#2-making-notes-the-short-version)
3. [The questions, one by one](#3-the-questions-one-by-one)
4. [Live lectures: breaks, stopping, and continuing later](#4-live-lectures-breaks-stopping-and-continuing-later)
5. [Your results](#5-your-results)
6. [Editing the notes](#6-editing-the-notes)
7. [How long it takes](#7-how-long-it-takes)
8. [Tips for better notes](#8-tips-for-better-notes)
9. [Troubleshooting](#9-troubleshooting)
10. [Command-line use (optional)](#10-command-line-use-optional)
11. [Common questions](#11-common-questions)

---

## 1. One-time setup

You need a Windows computer with an internet connection.

1. **Install Python** (version 3.10 or newer) from
   [python.org/downloads](https://www.python.org/downloads/). During installation, tick the option
   to **add Python to PATH**.
2. **Get the tool.** If you don't have the tool's folder yet, open its GitHub page, click the green
   **Code** button, choose **Download ZIP**, and extract it (for example, into Documents).
3. **Double-click `setup.bat`** in the tool's folder. It installs everything the tool needs. Wait
   for "Setup complete", then press any key to close the window.
4. **Install Claude Code and log in.** Install it from
   [claude.com/claude-code](https://claude.com/claude-code). Then open Command Prompt, type
   `claude`, press Enter, and log in with the Claude account that has Pro or Max. To check, type
   `/status`: the login method should name your plan, for example "Claude Max account". Type
   `/exit` to close it.

Microsoft Edge (built into Windows) or Google Chrome must be installed, because the tool uses it
to create the PDF.

The first time you transcribe a lecture, the tool downloads the speech-recognition model (about
1.6 GB). This happens automatically.

---

## 2. Making notes: the short version

1. Double-click **`run.bat`**.
2. Answer the questions. To give it a file, drag the file into the window and press Enter.
3. Wait. When the notes are ready, the PDF opens by itself. Press any key to close the window.

The rest of this guide explains each step in detail.

---

## 3. The questions, one by one

### "What do you have?"

Type a number and press Enter.

| Choice | Use it when |
|---|---|
| **1** A video or audio file | You have the lecture saved as a file (mp4, mkv, mov, mp3, m4a, wav and other common formats). |
| **2** A link | The lecture is online and opens without logging in, for example on YouTube. |
| **3** Playing live on this computer | You can only watch the lecture in a browser or app: a course site that needs a login, a live stream, Zoom or Teams. The tool records what your computer plays. |
| **4** In the room | You're at the lecture in person. The tool records with the microphone. |
| **5** Only a transcript | You already have the lecture's text (.txt, .srt, .vtt, .docx or .pdf). |

> **Tip:** If you can download the lecture or it has a public link, use choice 1 or 2 rather than
> 3. The tool then works from the file, so you don't have to keep the lecture playing, and you can
> take breaks whenever you like.

### The file or link

- **File:** drag it into the window (or type its full path), then press Enter.
- **Link:** paste it with Ctrl+V, then press Enter.

### "Do you also have a transcript?"

If the course gives you captions or a transcript, drag it in. The tool then uses both and
cross-checks them, which makes the notes more accurate. Otherwise, press Enter to skip.

### The lecture PDFs

Drag in the slides (or notes, or handout) and press Enter. Repeat for each PDF. When you've added
them all, press Enter on the empty line.

- The notes are much better with the PDF: Claude uses it to correct misheard terms and to explain
  the diagrams.
- Slides in PowerPoint? Open them in PowerPoint and save them as a PDF first
  (**File → Save As → PDF**).
- No PDF? Press Enter straight away. The notes will then be based on the lecture alone.

### Topic, accent and language (optional)

Press Enter to skip any of these. Filling in the first two helps the tool get technical words
right.

- **Topic:** for example `Organic Chemistry - Alkenes`.
- **Accent:** the lecturer's accent, for example `Indian`, `British`, `Nigerian` or `Chinese`.
- **Language:** leave it empty to detect it automatically. When transcription starts, the window
  shows `Detected language: ...`. If that's wrong, run the tool again and type the language code,
  such as `en` (English), `hi` (Hindi), `fr` (French) or `es` (Spanish).

The notes are written in English, whatever language the lecture is in. To change that, see
`--notes-language` in [Command-line use](#10-command-line-use-optional).

After the last question, the tool gets to work. Keep the window open until it finishes. For live
lectures, continue with the next section.

---

## 4. Live lectures: breaks, stopping, and continuing later

This section is for choices 3 and 4.

### Before you start

- **Pick your speakers or headphones first** (choice 3). The tool records the audio device that's
  active when recording starts, so don't switch devices during the lecture (for example, by
  connecting Bluetooth headphones).
- **Keep other sounds off** (choice 3). The tool records everything the computer plays, including
  notification sounds and other videos.
- **Stop the computer from sleeping.** Recording stops while the computer sleeps. Keep it plugged
  in, and set sleep to Never while you record (**Settings → System → Power**).
- **Play the lecture at normal speed** if you can. Sped-up speech is transcribed less accurately.
- **Sit near the lecturer** (choice 4). Distance, echo and chatter reduce accuracy.

### Recording

1. After the questions, wait until the window shows `>>> Recording ... <<<`.
2. Start the lecture.
3. About every 30 seconds, new lines of transcript appear in the window. That's how you know it's
   working.

### Pausing, stopping and continuing

The keys only work when the tool's window is active. You'll usually be in the browser watching the
lecture, so **click the tool window's title bar first** (or switch to it with Alt+Tab).

| To... | Do this |
|---|---|
| **Take a break** | Pause the video. Click the tool window and press **P**. It shows `PAUSED`. Nothing is recorded while paused, so you can use the computer normally. |
| **Come back** | Click the tool window and press **P** again. It shows `RESUMED`. Then press play on the video. |
| **Stop** | Click the tool window and press **Enter**. |

When you stop, the tool asks `Is the lecture finished?`

- **Y** (or just Enter): the lecture is finished. The tool re-checks the whole recording with a
  more accurate model, then writes the notes.
- **L**: save it and continue later. You can then close the window.

### Continuing another time

Double-click `run.bat` and choose **3** (or **4**). The tool lists your unfinished lectures. Type
the lecture's number (or type 0 to start a new lecture instead). Wait for `>>> Recording ... <<<`,
then press play. Your PDFs and settings are remembered, and the timestamps carry on from where you
stopped.

You can continue as many times as you need. When you finally answer **Y**, the notes cover every
part.

If the window gets closed by accident during a recording, what was recorded so far is kept. The
lecture appears in the list of unfinished lectures, and you can continue it the same way.

---

## 5. Your results

Everything is saved in the `output` folder inside the tool's folder. Each lecture gets its own
folder, named after the lecture (or its PDF) and the date, for example
`output\Week3_Slides_2026-09-27_1430\`.

| File | What it is |
|---|---|
| `..._notes.pdf` | The finished notes. This opens automatically. |
| `notes.md` | The same notes as text you can edit (see [Editing the notes](#6-editing-the-notes)). |
| `notes.html` | The same notes as a web page. |
| `transcript.txt` | The transcript, with timestamps like `[12:34]`. |
| `transcript_live.txt`, `lecture_recording_part1.wav`, ... | Live lectures only: the rough live transcript and the recordings. |

### What's in the notes

The notes follow the lecture section by section, with slide numbers and timestamps so you can find
the moment in the recording. They end with these sections:

- **Key Takeaways**
- **Important Definitions**
- **Important Formulas / Equations**
- **Exam / Review Questions**
- **Points Requiring Clarification**: anything that was unclear in the audio or disagrees with the
  slides. Read this section so you know what to double-check.

In `transcript.txt`, lines marked `[LOW CONFIDENCE - audio unclear]` were hard to hear.

---

## 6. Editing the notes

1. Open `notes.md` in a text editor (Notepad works).
2. Make your changes and save. Text between `$` signs is a formula.
3. Recreate the PDF. Open Command Prompt in the tool's folder and run:

   ```
   run.bat --render "output\<lecture folder>\notes.md"
   ```

**To open Command Prompt in the tool's folder:** open the folder in File Explorer, click the
address bar at the top, type `cmd`, and press Enter.

---

## 7. How long it takes

These are approximate times on a laptop without a graphics card (AMD Ryzen 7 5800U). Faster
computers take less time.

| Step | Approximate time |
|---|---|
| Transcribing a file or link | 35 minutes per hour of lecture |
| Live lecture | Records while the lecture plays. After you finish, the accurate re-check takes about 35 minutes per hour of recording. |
| Writing the notes | A few minutes |
| First use only | Downloading the speech model: about 1.6 GB, plus about 0.5 GB the first time you use live mode |

With a transcript (choice 5), only the notes step is needed, so it takes just a few minutes.

**To speed things up:** keep the laptop plugged in (battery saving slows it down) and close other
heavy programs. For transcription about 3 times faster but less accurate, add `--quality fast`
(see [Command-line use](#10-command-line-use-optional)).

---

## 8. Tips for better notes

- Always add the lecture's PDF.
- Fill in the topic and the lecturer's accent.
- If the course provides captions or a transcript, add them as well as the video.
- Read **Points Requiring Clarification** at the end of the notes, and check those parts against
  the lecture.

---

## 9. Troubleshooting

**"'python' is not recognized as an internal or external command"**
Python isn't installed, or wasn't added to PATH. Reinstall Python and tick the PATH option (see
[setup](#1-one-time-setup)).

**The tool asks you to paste an API key**
It couldn't find Claude Code. Install Claude Code and log in (setup step 4), then run the tool
again. Only enter a key if you want to pay per use.

**An error about logging in while the notes are being written**
Claude Code isn't logged in. Open Command Prompt, type `claude`, log in, then try again.

**You've reached your Claude usage limit**
Wait until your limit resets. Your transcript is already saved, and the window shows a command that
writes the notes without transcribing again. Run that command in Command Prompt, opened in the
tool's folder.

**Live lecture: no transcript lines appear**
Check that the lecture is playing, the video isn't muted, and the sound comes out of the device that
was active when recording started. Also check the window doesn't say `PAUSED`. To fix it without
losing anything, press Enter, type **L**, fix the problem, and then
[continue the lecture](#continuing-another-time).

**Pressing P or Enter does nothing**
The tool's window isn't active. Click its title bar first.

**"No speech was captured or transcribed"**
The recording or file had no clear speech in it. Check that the audio plays and that you chose the
right file.

**A link won't download**
Pages that need a login can't be downloaded. Play the lecture and use choice 3 instead, or
download the video yourself and use choice 1.

**Formulas in the PDF look like code, such as `$\alpha$`**
The PDF was created without an internet connection, which is needed to draw formulas. Reconnect,
then recreate the PDF with `run.bat --render` (see [Editing the notes](#6-editing-the-notes)).

**"PDF step failed"**
The notes are still saved as `notes.md` and `notes.html`. Recreate the PDF with `run.bat --render`,
or open `notes.html` in Edge and print it to PDF (Ctrl+P, then Save as PDF).

**Transcription is very slow, or the computer is sluggish**
Transcription uses a lot of processing power. Plug the laptop in, close other programs, or use
`--quality fast`.

---

## 10. Command-line use (optional)

Instead of answering the questions, you can give everything at once. Open Command Prompt in the
tool's folder (see [Editing the notes](#6-editing-the-notes)) and type `run.bat` followed by what
you have:

```
run.bat "C:\Lectures\week3.mp4" --pdf "C:\Lectures\week3_slides.pdf" --topic "Thermodynamics" --accent Indian
run.bat https://www.youtube.com/watch?v=VIDEO_ID --pdf "slides.pdf"
run.bat live --pdf "slides.pdf"
run.bat mic --pdf "slides.pdf"
run.bat --transcript "week3.srt" --pdf "slides.pdf" --pdf "handout.pdf"
```

If you leave out `--pdf`, the tool asks the remaining questions.

| Option | What it does |
|---|---|
| `--pdf FILE` | A lecture PDF. Repeat it for several PDFs. |
| `--transcript FILE` | A transcript you already have. |
| `--topic "TEXT"` | The course or lecture topic. |
| `--accent TEXT` | The lecturer's accent. |
| `--language CODE` | The spoken language, such as `en` or `hi` (default: detect automatically). |
| `--notes-language LANGUAGE` | The language to write the notes in (default: English). |
| `--quality fast`, `balanced` or `best` | Transcription speed against accuracy. `balanced` is the default. `fast` is about 3 times faster but less accurate. `best` is slower but the most accurate. |
| `--no-refine` | Live lectures: skip the accurate re-check at the end. |
| `--resume FOLDER` | Continue a saved live lecture (the same as choosing it from the list). |
| `--render NOTES.md` | Recreate the PDF from an edited `notes.md`. |
| `--claude-model sonnet` | Use a different Claude model (default: `opus`). |
| `--engine api` | Use an Anthropic API key instead of your subscription. This is billed per use. |
| `--out FOLDER` | Save results somewhere other than the `output` folder. |

`run.bat --help` lists all the options.

---

## 11. Common questions

**Is it really free?**
Yes, with a Claude Pro or Max subscription. Transcription runs on your computer, and the notes use
your subscription's normal usage allowance.

**What gets sent over the internet?**
The audio stays on your computer. The transcript and your PDFs are sent to Claude to write the
notes. With a link, the audio is downloaded from that website.

**How accurate are the notes?**
Speech recognition can mishear words, especially names and technical terms. Claude corrects many of
these using the slides, marks unclear parts instead of guessing, and lists them under Points
Requiring Clarification. Check anything important against the lecture or the slides.

**Can I use the computer while the tool works?**
Yes, but transcription makes it slower. During a live recording (choice 3), don't play other
sounds unless you've paused with **P**.
