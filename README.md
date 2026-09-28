# kugou-to-mp3-android

Termux/Android utility to detect KuGou-like local music files and convert decodable files into MP3.

Important: Do NOT use on DRM/encrypted files you are not allowed to convert.

## Quick start (Termux on Android)

1. Install Termux from F-Droid or other trusted source.
2. Open Termux and grant storage access:
   termux-setup-storage
   (Allow permission when prompted)

3. Install required packages:
   pkg update && pkg upgrade -y
   pkg install python ffmpeg git -y

4. Clone the repo:
   git clone https://github.com/yukaibo682/kugou-to-mp3-android
   cd kugou-to-mp3-android

5. (Optional) install Python helpers (not required):
   pip install --user -r requirements.txt
   (There are no mandatory pip deps for the included script)

6. Run the scanner/converter:
   python3 convert_kugou.py -i /sdcard/Music -o /sdcard/Music/converted -b 320k --normalize

   Flags:
   - `-i` input folder (default current dir)
   - `-o` output folder (default ./converted)
   - `-b` bitrate (default 320k)
   - `--normalize` apply loudnorm
   - `--overwrite` overwrite existing outputs
   - `-v` verbose logs

7. Check `converted/` for results. Files that were skipped as "可能受保护" are likely encrypted/non-decodable.

## Notes
- The script uses ffprobe to detect whether a file contains a decodable audio stream.
- Files with suspicious names (like containing `.kgg.` or extensions starting with `qmc`/`kgm`) are skipped and logged.
- If a file fails conversion but ffprobe says decodable, please paste ffprobe output and I can help debug.

## License
MIT
