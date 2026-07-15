#!/usr/bin/env python3
"""Verify one shared Markdown/HTML/audio visualization report manifest."""
import argparse, hashlib, json, re, sys
from pathlib import Path
KINDS=("audio","waveform","spectrogram","playback")
def check_file(root,row):
 p=(root/row["path"]).resolve()
 if root not in p.parents and p!=root: raise ValueError("report path escapes manifest root")
 if not p.is_file(): raise ValueError("missing report file: "+row["path"])
 if hashlib.sha256(p.read_bytes()).hexdigest()!=row["sha256"]: raise ValueError("hash mismatch: "+row["path"])
 return p
def verify(path):
 path=Path(path).resolve(); root=path.parent; data=json.loads(path.read_text())
 if data.get("schema_version")!=1: raise ValueError("schema_version must be 1")
 house=data.get("house_parameters",{})
 if house.get("sample_rate_hz")!=48000 or house.get("frequency_band_hz")!=[0,24000]: raise ValueError("house parameters require 48kHz/full-band 0-24kHz")
 md=check_file(root,data["outputs"]["markdown"]); html=check_file(root,data["outputs"]["html"])
 md_text=md.read_text(errors="replace"); html_text=html.read_text(errors="replace")
 for key,value in data.get("summary_stats",{}).items():
  if str(key) not in md_text or str(value) not in md_text or str(key) not in html_text or str(value) not in html_text: raise ValueError("summary stats missing from both outputs: "+key)
 groups={}
 for row in data.get("media",[]):
  if row.get("kind") not in KINDS: raise ValueError("invalid media kind")
  check_file(root,row); groups.setdefault(row.get("sample_id"),set()).add(row["kind"])
  link=row["path"]
  if link not in md_text or link not in html_text: raise ValueError("media link not bound in both outputs: "+link)
 if not groups or any(kinds!=set(KINDS) for kinds in groups.values()): raise ValueError("each sample requires 1:1 audio/waveform/spectrogram/playback")
 if not data.get("visual_evidence"): raise ValueError("visual evidence required")
 for row in data["visual_evidence"]: check_file(root,row)
 return {"samples":len(groups),"media":sum(map(len,groups.values()))}
def main():
 p=argparse.ArgumentParser(); p.add_argument("manifest"); a=p.parse_args(); print(json.dumps(verify(a.manifest),sort_keys=True))
if __name__=="__main__":
 try: main()
 except (ValueError,KeyError,json.JSONDecodeError) as e: print("report-manifest-verify:",e,file=sys.stderr); raise SystemExit(65)
