"""Generate the 30-second demo's narration in Md. Habibullah Sharif's own voice, cloned with F5-TTS.

Run from video/film (F5-TTS lives in its own environment, ~/.venvs/f5tts: f5-tts==1.1.22, CPU torch 2.15.0):
    python3 tools/clone_voice30.py <his recording> [--takes 2] [--speed 1.0]
    python3 tools/voice_human30.py assets/voice/raw/d30_clone_take1.wav --name d30_clone

The reference is the first 9.74 s of his WhatsApp voice note (the quietest stretch: no background voices in the
pauses), cleaned and resampled to 24 kHz, with its transcript. F5-TTS then reads the demo script (tools/vo_demo30.json,
"d30_human") in that voice. Everything runs locally; the model weights (SWivid/F5-TTS, F5TTS_v1_Base) are CC BY-NC 4.0.
The result is AI-generated audio and is credited as such on screen, in the description and in the file metadata.
"""
import argparse
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "assets" / "voice" / "raw"           # git-ignored: his recording never goes to GitHub
CLI = Path.home() / ".venvs" / "f5tts" / "bin" / "f5-tts_infer-cli"
REF_SPAN = (0.0, 9.74)
REF_TEXT = "We are Dreams of X, for NASA's Abandoned but not Forgotten challenge, we build the Moon Material Simulator."
TEXT = json.loads((ROOT / "tools" / "vo_demo30.json").read_text())["d30_human"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("recording")
    ap.add_argument("--takes", type=int, default=1)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--nfe", type=int, default=32, help="denoising steps: more is slower and a little cleaner")
    args = ap.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    ref = RAW / "d30_clone_ref.wav"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", args.recording, "-ss", str(REF_SPAN[0]),
                    "-t", str(REF_SPAN[1] - REF_SPAN[0]),
                    "-af", "highpass=f=80,afftdn=nr=12:nf=-50,loudnorm=I=-18:TP=-2,aresample=24000",
                    "-ac", "1", str(ref)], check=True)
    env = dict(os.environ, HF_HUB_DISABLE_TELEMETRY="1", HF_HUB_DISABLE_XET="1", WANDB_MODE="disabled", DO_NOT_TRACK="1",
               GRADIO_ANALYTICS_ENABLED="False", TOKENIZERS_PARALLELISM="false")
    for k in range(1, args.takes + 1):
        out = f"d30_clone_take{k}.wav"
        subprocess.run([str(CLI), "--model", "F5TTS_v1_Base", "--ref_audio", str(ref), "--ref_text", REF_TEXT,
                        "--gen_text", TEXT, "--output_dir", str(RAW), "--output_file", out, "--nfe_step", str(args.nfe),
                        "--speed", str(args.speed), "--device", "cpu", "--remove_silence"], check=True, env=env)
        print(f"wrote {(RAW / out).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
