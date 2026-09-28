#!/usr/bin/env python3
"""
convert_kugou.py
Scan a directory, detect KuGou-like files, use ffprobe to check decodability,
and convert decodable files to 320k MP3 using ffmpeg while preserving metadata.
"""

import argparse
import json
import logging
import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path

PROTECTED_PATTERNS = [
    re.compile(r'\.qmc', re.IGNORECASE),
    re.compile(r'\.kgm$', re.IGNORECASE),
    re.compile(r'\.kgg\.', re.IGNORECASE),  # filename like name.kgg.flac
]

def is_probably_protected(name: str) -> bool:
    for p in PROTECTED_PATTERNS:
        if p.search(name):
            return True
    return False

def ffprobe_streams(path: Path):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "stream=index,codec_type,codec_name,channels,sample_rate",
        "-print_format", "json",
        str(path)
    ]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
        return json.loads(out)
    except subprocess.CalledProcessError:
        return None
    except json.JSONDecodeError:
        return None

def is_decodable(path: Path) -> bool:
    info = ffprobe_streams(path)
    if not info:
        return False
    streams = info.get("streams", [])
    for s in streams:
        if s.get("codec_type") == "audio" and s.get("codec_name"):
            return True
    return False

def convert_to_mp3(infile: Path, outfile: Path, bitrate: str, normalize: bool) -> bool:
    outfile.parent.mkdir(parents=True, exist_ok=True)
    base_cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(infile)]
    if normalize:
        base_cmd += ["-af", "loudnorm=I=-14:LRA=11:TP=-1.5"]
    base_cmd += ["-c:a", "libmp3lame", "-b:a", bitrate, "-map_metadata", "0", str(outfile)]
    try:
        subprocess.check_call(base_cmd)
        return True
    except subprocess.CalledProcessError:
        return False

def walk_and_convert(src: Path, dst: Path, bitrate: str, normalize: bool, overwrite: bool):
    stats = {"total":0, "skipped_protected":0, "skipped_unsupported":0, "converted":0, "failed":0}
    for p in src.rglob("*"):
        if not p.is_file():
            continue
        stats["total"] += 1
        name = p.name
        if is_probably_protected(name):
            logging.info("SKIP (可能受保护): %s", p)
            stats["skipped_protected"] += 1
            continue
        # Quick decodability check
        if not is_decodable(p):
            logging.info("UNSUPPORTED / 加密: %s", p)
            stats["skipped_unsupported"] += 1
            continue
        rel = p.relative_to(src)
        outp = dst.joinpath(rel).with_suffix(".mp3")
        if outp.exists() and not overwrite:
            logging.info("Skipping (exists): %s", outp)
            continue
        logging.info("Converting: %s -> %s", p, outp)
        ok = convert_to_mp3(p, outp, bitrate, normalize)
        if ok:
            stats["converted"] += 1
        else:
            logging.warning("FAILED: %s", p)
            stats["failed"] += 1
    logging.info("Done. stats: %s", stats)
    return stats

def check_programs():
    for prog in ("ffmpeg", "ffprobe"):
        if shutil.which(prog) is None:
            raise RuntimeError(f"Required program not found in PATH: {prog}")

def main():
    parser = argparse.ArgumentParser(description="Detect and convert KuGou-like files to MP3 (Termux/Android)")
    parser.add_argument("-i", "--input", type=Path, default=Path("."), help="Input directory to scan")
    parser.add_argument("-o", "--output", type=Path, default=Path("converted"), help="Output directory")
    parser.add_argument("-b", "--bitrate", default="320k", help="Target audio bitrate (e.g. 320k)")
    parser.add_argument("--normalize", action="store_true", help="Apply loudnorm normalization")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing outputs")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    try:
        check_programs()
    except RuntimeError as e:
        logging.error(str(e))
        return

    src = args.input.resolve()
    dst = args.output.resolve()
    logging.info("Scanning %s -> %s", src, dst)
    walk_and_convert(src, dst, args.bitrate, args.normalize, args.overwrite)

if __name__ == "__main__":
    main()
