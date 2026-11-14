"""Write the YouTube subtitle file for the 30-second demo.

Run from video/film:  python3 tools/srt_demo30.py   # writes ../youtube/demo30/captions_en.srt

Same lines and timings as the captions burned into the video (CAPTION_LINES in tools/build_demo30.py),
at most two lines of 42 characters per cue.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_demo30 import ROOT, caption_cues  # noqa: E402
from srt import stamp, two_lines  # noqa: E402

OUT = ROOT.parent / "youtube" / "demo30" / "captions_en.srt"


KEEP = "Abandoned but not Forgotten"   # never split the challenge name across lines


def lines_for(text):
    if KEEP in text and len(text) > 42:
        a, _, b = text.partition(KEEP)
        if a.strip() and len(KEEP + b) <= 42:
            return a.strip() + "\n" + KEEP + b
    return two_lines(text)


def main():
    lines = []
    for i, (a, b, text) in enumerate(caption_cues()):
        lines += [str(i + 1), f"{stamp(a)} --> {stamp(b)}", lines_for(text), ""]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines))
    print(f"{len(lines) // 4} cues -> {OUT}")


if __name__ == "__main__":
    main()
