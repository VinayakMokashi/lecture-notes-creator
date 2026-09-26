"""Speech-to-text with faster-whisper: saved media files and live audio capture."""

import os
import queue
import sys
import threading
import time
import wave
import warnings

import numpy as np

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

SAMPLE_RATE = 16000

# Friendly quality presets -> Whisper model names.
QUALITY_MODELS = {
    "fast": "small",
    "balanced": "large-v3-turbo",
    "best": "large-v3",
}

# Segments below these confidence thresholds get flagged in the transcript.
LOW_LOGPROB = -1.0
HIGH_COMPRESSION = 2.4

_model_cache = {}


def load_model(name):
    if name not in _model_cache:
        from faster_whisper import WhisperModel

        print(f"Loading Whisper model '{name}' (first run downloads it)...")
        try:
            import torch

            cuda = torch.cuda.is_available()
        except ImportError:
            cuda = False
        device, compute = ("cuda", "float16") if cuda else ("cpu", "int8")
        _model_cache[name] = WhisperModel(
            name, device=device, compute_type=compute, cpu_threads=os.cpu_count() or 4
        )
    return _model_cache[name]


def build_initial_prompt(topic=None, glossary=None, accent=None):
    """Whisper's initial prompt biases it toward the lecture's vocabulary and spelling."""
    parts = ["This is a university lecture"]
    if topic:
        parts[0] += f" on {topic}"
    if accent:
        parts[0] += f", spoken with a {accent} accent"
    parts[0] += "."
    if glossary:
        parts.append("Terms used: " + ", ".join(glossary) + ".")
    prompt = " ".join(parts)
    return prompt[:900]


def fmt_ts(seconds):
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def _format_segment(seg, offset=0.0):
    text = seg.text.strip()
    if not text:
        return None
    flagged = seg.avg_logprob < LOW_LOGPROB or seg.compression_ratio > HIGH_COMPRESSION
    line = f"[{fmt_ts(seg.start + offset)}] {text}"
    if flagged:
        line += "  [LOW CONFIDENCE - audio unclear]"
    return line


def transcribe_file(path, model_name, language=None, initial_prompt=None):
    """Transcribe an audio or video file. Returns (transcript_text, detected_language)."""
    model = load_model(model_name)
    segments, info = model.transcribe(
        path,
        language=language,
        initial_prompt=initial_prompt,
        vad_filter=True,
        beam_size=5,
        condition_on_previous_text=False,
    )
    print(
        f"Detected language: {info.language} ({info.language_probability:.0%}); "
        f"audio length {fmt_ts(info.duration)}"
    )
    lines = []
    started = time.time()
    for seg in segments:
        line = _format_segment(seg)
        if line:
            lines.append(line)
        pct = min(seg.end / max(info.duration, 1), 1.0)
        elapsed = time.time() - started
        eta = elapsed / pct - elapsed if pct > 0 else 0
        sys.stdout.write(f"\r  Transcribing... {pct:5.1%}  (about {fmt_ts(eta)} left)   ")
        sys.stdout.flush()
    print("\r  Transcribing... done." + " " * 30)
    return "\n".join(lines), info.language


# ---------------------------------------------------------------------------
# Live capture
# ---------------------------------------------------------------------------

def _quietest_cut(chunk, search_seconds=5.0, window=0.3):
    """Index at which to cut the chunk: the quietest spot in its last few seconds,
    so words are less likely to be split between chunks."""
    win = int(window * SAMPLE_RATE)
    start = max(0, len(chunk) - int(search_seconds * SAMPLE_RATE))
    best_i, best_rms = len(chunk), None
    for i in range(start, len(chunk) - win, win // 2):
        rms = float(np.sqrt(np.mean(chunk[i : i + win] ** 2)))
        if best_rms is None or rms < best_rms:
            best_i, best_rms = i + win // 2, rms
    return best_i


def live_transcribe(source, wav_path, transcript_path, model_name, language=None,
                    initial_prompt=None, chunk_seconds=30):
    """Record from the speakers (loopback, i.e. whatever the browser is playing) or the
    microphone, transcribing in chunks as the lecture goes. Stops when Enter is pressed.
    Returns (transcript_text, detected_language)."""
    import soundcard as sc

    warnings.filterwarnings("ignore", category=sc.SoundcardRuntimeWarning)

    if source == "mic":
        device = sc.default_microphone()
    else:
        device = sc.get_microphone(id=str(sc.default_speaker().name), include_loopback=True)
    print(f"Recording from: {device.name}")

    model = load_model(model_name)
    stop = threading.Event()
    chunks = queue.Queue()
    lines = []
    detected = {"lang": language}

    def worker():
        prev_tail = ""
        while True:
            item = chunks.get()
            if item is None:
                return
            offset, audio = item
            if np.max(np.abs(audio)) < 1e-3:  # silence
                continue
            prompt = " ".join(p for p in (initial_prompt, prev_tail) if p)[-900:] or None
            segments, info = model.transcribe(
                audio,
                language=detected["lang"],
                initial_prompt=prompt,
                vad_filter=True,
                beam_size=5,
                condition_on_previous_text=False,
            )
            if detected["lang"] is None and info.language_probability > 0.8:
                detected["lang"] = info.language
            for seg in segments:
                line = _format_segment(seg, offset)
                if line:
                    lines.append(line)
                    print("  " + line)
                    with open(transcript_path, "a", encoding="utf-8") as f:
                        f.write(line + "\n")
                    prev_tail = seg.text.strip()[-200:]

    t = threading.Thread(target=worker, daemon=True)
    t.start()

    def wait_for_enter():
        try:
            input()
        except EOFError:
            pass
        stop.set()

    threading.Thread(target=wait_for_enter, daemon=True).start()
    print("\n>>> Recording. Start (or keep) the lecture playing. Press ENTER here to stop. <<<\n")

    buffer = np.zeros(0, dtype=np.float32)
    buffer_start = 0.0
    with wave.open(wav_path, "wb") as wav, device.recorder(samplerate=SAMPLE_RATE, channels=1) as rec:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        try:
            while not stop.is_set():
                data = rec.record(numframes=SAMPLE_RATE // 2).reshape(-1).astype(np.float32)
                wav.writeframes((np.clip(data, -1, 1) * 32767).astype(np.int16).tobytes())
                buffer = np.concatenate([buffer, data])
                if len(buffer) >= chunk_seconds * SAMPLE_RATE:
                    cut = _quietest_cut(buffer)
                    chunks.put((buffer_start, buffer[:cut].copy()))
                    buffer_start += cut / SAMPLE_RATE
                    buffer = buffer[cut:]
        except KeyboardInterrupt:
            pass
    if len(buffer):
        chunks.put((buffer_start, buffer))
    chunks.put(None)
    print("\nStopped recording. Finishing the last chunks...")
    t.join()
    return "\n".join(lines), detected["lang"]
