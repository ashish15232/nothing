
"""Diagnostic probe for the Avica runner method.

Replaces the pack's blind-click setup.py. Takes real screenshots at each
stage, uploads them, and reports what actually exists on the VM.
Nothing here guesses coordinates.
"""
import glob
import os
import subprocess
import sys
import time

import pyautogui
import requests

GOFILE = "https://store1.gofile.io/uploadFile"


def shot(tag):
    """Screenshot the desktop and upload it. Prints a public link."""
    name = f"{tag}.png"
    try:
        pyautogui.screenshot().save(name)
    except Exception as e:
        print(f"SHOT {tag}: SCREENSHOT FAILED {type(e).__name__}: {e}", flush=True)
        return
    try:
        with open(name, "rb") as f:
            r = requests.post(GOFILE, files={"file": f}, timeout=120)
        j = r.json()
        if j.get("status") == "ok":
            print(f"SHOT {tag}: {j['data']['downloadPage']}", flush=True)
        else:
            print(f"SHOT {tag}: upload rejected {j}", flush=True)
    except Exception as e:
        print(f"SHOT {tag}: UPLOAD FAILED {type(e).__name__}: {e}", flush=True)


def find_avica():
    pats = [
        r"C:\Program Files*\Avica*\*.exe",
        r"C:\Program Files*\*Avica*\*.exe",
        r"C:\Program Files*\Avica.exe",
        r"C:\Users\*\AppData\Local\*Avica*\*.exe",
        r"C:\Users\*\AppData\Roaming\*Avica*\*.exe",
    ]
    found = []
    for p in pats:
        found += glob.glob(p)
    return sorted(set(found))


def avica_procs():
    try:
        import psutil
    except ImportError:
        return ["psutil missing"]
    out = []
    for proc in psutil.process_iter(["name", "pid"]):
        try:
            if "avica" in (proc.info["name"] or "").lower():
                out.append(f"{proc.info['name']}({proc.info['pid']})")
        except Exception:
            pass
    return out


print("=" * 60, flush=True)
print("python:", sys.version.replace("\n", " "), flush=True)
print("cwd:", os.getcwd(), flush=True)
import PIL
print("Pillow:", PIL.__version__, flush=True)
print("=" * 60, flush=True)

shot("01-desktop-before-install")
print("program files entries:", flush=True)
for root in (r"C:\Program Files", r"C:\Program Files (x86)"):
    try:
        print(f"  {root}:", os.listdir(root)[:40], flush=True)
    except Exception as e:
        print(f"  {root}: {e}", flush=True)

exe = os.path.abspath("Avica_setup.exe")
print("installer:", exe, os.path.getsize(exe), "bytes", flush=True)

# Try silent switches; fall back to a plain launch (GUI).
for args in (["/S"], ["/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"], ["/silent"], []):
    print(f"--- install attempt {args or '[no args -> GUI]'}", flush=True)
    try:
        p = subprocess.run(
            [exe] + args,
            capture_output=True,
            text=True,
            timeout=240,
        )
        print("    rc:", p.returncode, "out:", (p.stdout or "")[-400:], "err:", (p.stderr or "")[-400:], flush=True)
    except subprocess.TimeoutExpired:
        print("    timed out waiting for installer (GUI likely waiting on a click)", flush=True)
    except Exception as e:
        print(f"    launch failed: {type(e).__name__}: {e}", flush=True)
    time.sleep(8)
    cands = find_avica()
    if cands:
        print("    INSTALLED:", cands, flush=True)
        break
    print("    nothing found yet", flush=True)

shot("02-desktop-after-install")

cands = find_avica()
print("final exe candidates:", cands, flush=True)
print("avica processes:", avica_procs(), flush=True)

if cands:
    print(f"--- launching {cands[0]}", flush=True)
    try:
        subprocess.Popen([cands[0]])
    except Exception as e:
        print(f"    launch failed: {type(e).__name__}: {e}", flush=True)
    time.sleep(25)
    shot("03-desktop-avica-launched")
    print("avica processes:", avica_procs(), flush=True)

shot("04-desktop-final")
print("DONE", flush=True)
