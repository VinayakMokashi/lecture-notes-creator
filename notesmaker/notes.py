"""Generating study notes with Claude from transcript(s) + course material.

Two engines: Claude Code (uses the Claude subscription it's logged in with; the default)
and the Anthropic API (needs an API key, billed per use)."""

import base64
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time

MODEL = "claude-opus-5"
MAX_TOKENS = 64000
# Keep base64-encoded PDFs comfortably under the 32 MB request limit.
MAX_PDF_BYTES = 22 * 1024 * 1024
MAX_PDF_PAGES = 600

SYSTEM_PROMPT = """You are an expert lecture assistant. You turn a lecture transcript and the \
accompanying course material into comprehensive, accurate study notes that a student can learn \
from without rewatching the lecture.

The goal is not to transcribe the lecture or summarise the slides. Cross-reference the two: the \
lecturer often explains concepts only briefly mentioned on the slides, gives examples that are \
not written anywhere, explains diagrams, adds context and interpretations, and emphasises what \
matters for the exam. Capture that spoken content, and use the course material to clarify and \
supplement it. Do not simply reproduce the PDF.

Transcript handling:
- The transcript was produced by speech recognition (or supplied by the student) and contains \
errors. Correct obvious mistakes, especially technical terms, names, equations, symbols, code \
and abbreviations, using the course material and the lecture context. Keep the lecturer's accent \
in mind: many errors are sound-alike substitutions.
- Lines marked [LOW CONFIDENCE] were unclear in the audio. Use them only when the context makes \
their meaning clear; otherwise list them under Points Requiring Clarification.
- Never invent content that was not said or written. Where something cannot be recovered, say so.
- If the transcript and the course material disagree, decide whether it is likely a transcription \
error. Do not silently change information: note the discrepancy, and flag anything that remains \
uncertain.

Writing the notes:
- Follow the logical structure of the lecture, with clear headings and subheadings.
- Explain concepts in enough depth to study from. Include, where applicable: key concepts, \
definitions, detailed explanations, important examples, formulas, step-by-step derivations, \
explanations of diagrams and figures (refer to the slide/page number), code or pseudocode, \
observations the lecturer made, connections between concepts, practical applications, \
assumptions and limitations, and anything the lecturer emphasised or hinted is exam-relevant.
- Avoid unnecessary repetition.
- Use bullet points, numbered steps, and tables where they make things clearer.
- Mark important terms with bold, and use blockquote callouts for emphasis, e.g. \
"> **Lecturer emphasis:** ..." or "> **Exam tip:** ...".
- Write all mathematics in LaTeX: $...$ inline and $$...$$ on their own lines for display \
equations. Put code in fenced code blocks with a language tag.

Output format: GitHub-flavoured Markdown only, with no preamble or closing remarks. Start with \
a single "# " title line naming the lecture, then a short italic line summarising what the \
lecture covers. After the main notes, finish with these sections in this order:
## Key Takeaways
## Important Definitions
## Important Formulas / Equations
## Exam / Review Questions
## Points Requiring Clarification
(Include transcript timestamps such as [12:34] where they help the student find the moment.)"""


def _material_blocks(materials):
    """PDFs go in as document blocks so Claude sees figures too; oversized ones as text."""
    blocks, total = [], 0
    for mat in materials:
        total += len(mat.data)
        if total <= MAX_PDF_BYTES and mat.pages <= MAX_PDF_PAGES:
            blocks.append({
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": base64.standard_b64encode(mat.data).decode("ascii"),
                },
                "title": mat.path.name,
            })
        else:
            print(f"  Note: {mat.path.name} is too large to send as a PDF; sending its text only.")
            blocks.append({
                "type": "text",
                "text": f"<course_material name=\"{mat.path.name}\">\n{mat.text}\n</course_material>",
            })
    return blocks


def build_request_text(transcripts, info):
    parts = []
    context = [f"- {k}: {v}" for k, v in info.items() if v]
    if context:
        parts.append("Lecture details:\n" + "\n".join(context))
    for label, text in transcripts:
        parts.append(f"<transcript source=\"{label}\">\n{text}\n</transcript>")
    if len(transcripts) > 1:
        parts.append(
            "There are several transcripts of the same lecture. Treat the student-supplied one as "
            "the primary source, and use the others to fill gaps and correct its errors."
        )
    parts.append(
        "Create the study notes for this lecture, combining the transcript with the attached "
        "course material." if info.get("Course material") else
        "Create the study notes for this lecture. No course material was supplied, so rely on the "
        "transcript alone and flag uncertain technical terms rather than guessing."
    )
    return "\n\n".join(parts)


def find_claude_code():
    return shutil.which("claude")


def _clean_notes(text):
    """Drop any chatter before the notes' '# Title' line."""
    match = re.search(r"^# ", text, re.M)
    return (text[match.start():] if match else text).strip()


def generate_notes_claude_code(transcripts, materials, info, work_dir, model="opus"):
    """Write the notes with the Claude Code CLI, which uses the Claude subscription it is
    logged in with (no API key or per-lecture charge). Claude reads the PDFs itself with
    its Read tool (read-only: it can't change any files). Returns the notes as Markdown."""
    claude = find_claude_code()
    if not claude:
        raise RuntimeError("Claude Code isn't installed (see https://claude.com/claude-code), "
                           "or use --engine api.")

    request = []
    if materials:
        request.append(
            "Course material - read every page of these PDFs with the Read tool before writing "
            "(for PDFs longer than 20 pages, read them in page ranges of at most 20):\n"
            + "\n".join(f"- {m.path.resolve()} ({m.pages} pages)" for m in materials)
        )
    request.append(build_request_text(transcripts, info))
    request.append("Reply with only the finished notes in Markdown, with no preamble and no "
                   "comments about the files or your process.")

    env = os.environ.copy()
    # Make sure the subscription login is used rather than any API key, and allow this
    # to run from inside another Claude Code session.
    for key in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDECODE"):
        env.pop(key, None)
    env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] = str(MAX_TOKENS)

    cmd = [
        claude, "-p",
        "--output-format", "json",
        "--model", model,
        "--system-prompt", SYSTEM_PROMPT,
        "--tools", "Read",
        "--allowedTools", "Read",
        "--strict-mcp-config",
        "--no-session-persistence",
    ]
    for folder in sorted({str(m.path.resolve().parent) for m in materials}):
        cmd += ["--add-dir", folder]

    print(f"Writing notes with Claude Code (your Claude subscription, model: {model}). "
          "This usually takes a few minutes...")
    proc = subprocess.Popen(
        cmd, cwd=work_dir, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, encoding="utf-8", errors="replace",
    )
    result = {}

    def communicate():
        result["out"], result["err"] = proc.communicate("\n\n".join(request))

    worker = threading.Thread(target=communicate, daemon=True)
    worker.start()
    started = time.time()
    while worker.is_alive():
        worker.join(1)
        sys.stdout.write(f"\r  Claude is working... {int(time.time() - started) // 60}:"
                         f"{int(time.time() - started) % 60:02d} elapsed ")
        sys.stdout.flush()
    print()

    out, err = result.get("out", ""), result.get("err", "")
    try:
        data = json.loads(out)
    except ValueError:
        raise RuntimeError(f"Claude Code failed: {(err or out).strip()[:800]}")
    if data.get("is_error") or data.get("subtype") != "success":
        raise RuntimeError(f"Claude Code reported an error: {str(data.get('result'))[:800]}")
    notes = _clean_notes(data.get("result") or "")
    if not notes:
        raise RuntimeError("Claude Code returned empty notes.")
    return notes


def generate_notes(transcripts, materials, info):
    """Write the notes with the Anthropic API (billed per use to the API key).
    transcripts: list of (label, text). Returns the notes as Markdown."""
    import anthropic

    client = anthropic.Anthropic()
    content = _material_blocks(materials)
    content.append({"type": "text", "text": build_request_text(transcripts, info)})

    print(f"Sending to Claude ({MODEL}). Large lectures can take several minutes...")
    chars = 0
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        messages=[{"role": "user", "content": content}],
    ) as stream:
        sys.stdout.write("  Claude is reading the lecture...")
        sys.stdout.flush()
        for text in stream.text_stream:
            chars += len(text)
            if chars % 500 < len(text):
                sys.stdout.write(f"\r  Writing notes... {chars:,} characters so far   ")
                sys.stdout.flush()
        message = stream.get_final_message()
    print(f"\r  Writing notes... done ({chars:,} characters).        ")

    if message.stop_reason == "refusal":
        raise RuntimeError("Claude declined to produce notes for this content.")
    notes = "".join(b.text for b in message.content if b.type == "text").strip()
    if message.stop_reason == "max_tokens":
        print("  Warning: the notes hit the length limit and may be cut off at the end.")
        notes += "\n\n> **Note:** these notes reached the maximum length and may be incomplete."
    return notes
