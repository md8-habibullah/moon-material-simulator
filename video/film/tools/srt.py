"""Write the YouTube subtitle file from the narration's word timings.

Run from video/film after tools/build.py:
    python3 tools/srt.py            # writes ../youtube/captions_en.srt

One cue per sentence (long sentences split at a comma or colon), at most two lines of 42 characters.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402  (module level computes the voices and scene starts; main() is not run)

OUT = build.ROOT.parent / "youtube" / "captions_en.srt"
MAX = 84


def stamp(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def two_lines(text):
    if len(text) <= 42:
        return text
    words, best = text.split(), None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        score = max(len(a), len(b))
        if best is None or score < best[0]:
            best = (score, a + "\n" + b)
    return best[1]


def chunks(words):
    """Group words into cues: break after sentence ends, and after , : ; once a cue gets long."""
    cur = []
    for w in words:
        cur.append(w)
        text = " ".join(x["text"] for x in cur)
        if re.search(r"[.?!]$", w["text"]) or (len(text) > 40 and re.search(r"[,:;]$", w["text"])) or len(text) > MAX - 8:
            yield cur
            cur = []
    if cur:
        yield cur


def main():
    cues = []
    for sid in build.ORDER:
        base = build.STARTS[sid] + build.LEAD
        for group in chunks(build.VOICES[sid].words):
            cues.append((base + group[0]["start"], base + group[-1]["end"] + 0.25, " ".join(w["text"] for w in group)))
    lines = []
    for i, (a, b, text) in enumerate(cues):
        if i + 1 < len(cues):
            b = min(b, cues[i + 1][0] - 0.04)
        lines += [str(i + 1), f"{stamp(a)} --> {stamp(b)}", two_lines(text), ""]
    OUT.write_text("\n".join(lines))
    print(f"{len(cues)} cues → {OUT}")


if __name__ == "__main__":
    main()
