#!/usr/bin/env python3
# decision.py

import argparse
import queue
import sys
import json
import sounddevice as sd
from vosk import Model, KaldiRecognizer

q = queue.Queue()

def int_or_str(text):
    try:
        return int(text)
    except ValueError:
        return text

def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("-l", "--list-devices", action="store_true",
                    help="show list of audio devices and exit")
args, remaining = parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    sys.exit(0)

parser = argparse.ArgumentParser(parents=[parser])
parser.add_argument("-f", "--filename", type=str, metavar="FILENAME",
                    help="optional: dump raw audio to a file")
parser.add_argument("-d", "--device", type=int_or_str,
                    help="input device (numeric ID or substring)")
parser.add_argument("-r", "--samplerate", type=int, help="sampling rate")
parser.add_argument("-m", "--model", type=str,
                    help="language model code; default en-us")
args = parser.parse_args(remaining)

try:
    if args.samplerate is None:
        device_info = sd.query_devices(args.device, "input")
        args.samplerate = int(device_info["default_samplerate"])

    # Load vosk model (assumes model installed locally)
    model = Model(lang=args.model or "en-us")

    dump_fn = open(args.filename, "wb") if args.filename else None

    with sd.RawInputStream(samplerate=args.samplerate,
                           blocksize=8000,
                           device=args.device,
                           dtype="int16",
                           channels=1,
                           callback=callback):
        print("#" * 60, file=sys.stderr)
        print("Listening… say: yes / no / there / bye (Ctrl+C to quit)", file=sys.stderr)
        print("#" * 60, file=sys.stderr)

        rec = KaldiRecognizer(model, args.samplerate)

        while True:
            data = q.get()
            if dump_fn:
                dump_fn.write(data)

            # If a full utterance boundary is detected:
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = (result.get("text") or "").strip().lower()

                # Ignore empty recognitions
                if not text:
                    continue

                # Optional: print what was heard to stderr for debugging
                print(f"[heard] {text}", file=sys.stderr)

                # Look for keywords; print ONLY the decision word to stdout
                if "yes" in text:
                    print("yes")
                    break
                if "no" in text:
                    print("no")
                    break
                if "there" in text:
                    print("there")
                    break
                if "bye" in text:
                    print("bye")
                    break

            else:
                # Partial results can be used if you want faster reaction:
                # partial = json.loads(rec.PartialResult()).get("partial","")
                # (we ignore partials here)
                pass

except KeyboardInterrupt:
    print("\nDone", file=sys.stderr)
    sys.exit(0)
except Exception as e:
    # Print the error to stderr and exit non-zero
    print(f"Error: {type(e).__name__}: {e}", file=sys.stderr)
    sys.exit(1)
finally:
    try:
        if dump_fn:
            dump_fn.close()
    except NameError:
        pass
