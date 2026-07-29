#!/usr/bin/env python3
"""Verify one shared Markdown/HTML/audio visualization report manifest."""
import argparse, hashlib, json, re, sys
from pathlib import Path
KINDS=("audio","waveform","spectrogram","playback")
ROLES=("canonical","summary","interactive","navigation")
BUNDLE_KEYS=("title","primary_representation_id","representations","equivalence_groups")
REPR_KEYS=("id","format","roles","output","file","section_order")
GROUP_KEYS=("id","representation_ids","section_order")
ID_PAT="^[a-z0-9][a-z0-9-]*$"; FORMAT_PAT="^[a-z0-9][a-z0-9.+-]*$"
def check_file(root,row):
 p=(root/row["path"]).resolve()
 if root not in p.parents and p!=root: raise ValueError("report path escapes manifest root")
 if not p.is_file(): raise ValueError("missing report file: "+row["path"])
 if hashlib.sha256(p.read_bytes()).hexdigest()!=row["sha256"]: raise ValueError("hash mismatch: "+row["path"])
 return p
def load_bundle(root,data,texts):
 b=data["bundle"]; title=b.get("title")
 if not isinstance(title,str) or not title: raise ValueError("bundle title must be a non-empty string")
 reps={}; claimed=set(); outputs=data["outputs"]
 for row in b.get("representations",[]):
  if set(row)-set(REPR_KEYS): raise ValueError("invalid representation property")
  rid=row.get("id"); fmt=row.get("format"); roles=row.get("roles")
  if not isinstance(rid,str) or not re.fullmatch(ID_PAT,rid) or rid in reps: raise ValueError("invalid or duplicate representation id")
  if not isinstance(fmt,str) or not re.fullmatch(FORMAT_PAT,fmt): raise ValueError("invalid representation format: "+str(rid))
  if not isinstance(roles,list) or not roles or len(set(roles))!=len(roles) or any(role not in ROLES for role in roles): raise ValueError("invalid representation roles: "+rid)
  has_output="output" in row; has_file="file" in row
  if has_output==has_file: raise ValueError("representation requires exactly one output or file: "+rid)
  if has_output:
   key=row["output"]
   if key not in outputs: raise ValueError("representation output is not declared: "+rid)
   if key in claimed: raise ValueError("output claimed more than once: "+key)
   claimed.add(key); source=outputs[key]; p=check_file(root,source); path=source["path"]; text=texts[key]
  else:
   source=row["file"]; p=check_file(root,source); path=source["path"]
   if any(p==(root/outputs[key]["path"]).resolve() for key in outputs): raise ValueError("inline file duplicates output path: "+path)
   text=p.read_text(errors="replace")
  order=row.get("section_order"); reps[rid]=(set(roles),text,path,order)
 if claimed!=set(outputs): raise ValueError("every output must be claimed exactly once")
 pid=b.get("primary_representation_id")
 if pid not in reps: raise ValueError("unknown primary representation: "+str(pid))
 groups=[]; ids=set()
 for group in b.get("equivalence_groups",[]):
  if set(group)-set(GROUP_KEYS): raise ValueError("invalid equivalence group property")
  gid=group.get("id"); members=group.get("representation_ids"); order=group.get("section_order")
  if not isinstance(gid,str) or not re.fullmatch(ID_PAT,gid) or gid in ids: raise ValueError("invalid or duplicate equivalence group id")
  if not isinstance(members,list) or len(members)<2 or len(set(members))!=len(members) or any(member not in reps for member in members): raise ValueError("invalid equivalence group members")
  if not isinstance(order,list) or not order or len(set(order))!=len(order) or any(not isinstance(section,str) or not section for section in order): raise ValueError("invalid equivalence group section order")
  ids.add(gid); groups.append((set(members),order))
 return title,pid,reps,groups
def verify(path):
 path=Path(path).resolve(); root=path.parent; data=json.loads(path.read_text())
 if data.get("schema_version")!=1: raise ValueError("schema_version must be 1")
 house=data.get("house_parameters",{})
 if house.get("sample_rate_hz")!=48000 or house.get("frequency_band_hz")!=[0,24000]: raise ValueError("house parameters require 48kHz/full-band 0-24kHz")
 md=check_file(root,data["outputs"]["markdown"]); html=check_file(root,data["outputs"]["html"])
 md_text=md.read_text(errors="replace"); html_text=html.read_text(errors="replace")
 texts={"markdown":md_text,"html":html_text}; has_bundle="bundle" in data
 if has_bundle:
  title,pid,reps,eq_groups=load_bundle(root,data,texts); stat_ids={pid}|{rid for rid,(roles,*_) in reps.items() if roles&{"canonical","summary"}}; nav_ids={rid for rid,(roles,*_) in reps.items() if "navigation" in roles}; play_ids={rid for rid,(roles,*_) in reps.items() if "interactive" in roles}; canon_ids={rid for rid,(roles,*_) in reps.items() if "canonical" in roles}
  if title not in reps[pid][1]: raise ValueError("bundle title missing from primary representation: "+pid)
  for rid in nav_ids:
   if title not in reps[rid][1] or reps[pid][2] not in reps[rid][1]: raise ValueError("navigation representation must carry the bundle title and a link to the primary: "+rid)
  if not play_ids: raise ValueError("a media bundle requires one interactive representation")
 for key,value in data.get("summary_stats",{}).items():
  if has_bundle:
   for rid in stat_ids:
    if str(key) not in reps[rid][1] or str(value) not in reps[rid][1]: raise ValueError("summary stats missing from representation "+rid+": "+str(key))
  elif str(key) not in md_text or str(value) not in md_text or str(key) not in html_text or str(value) not in html_text: raise ValueError("summary stats missing from both outputs: "+key)
 groups={}
 for row in data.get("media",[]):
  if row.get("kind") not in KINDS: raise ValueError("invalid media kind")
  check_file(root,row); groups.setdefault(row.get("sample_id"),set()).add(row["kind"])
  link=row["path"]
  if has_bundle:
   for rid in play_ids:
    if link not in reps[rid][1]: raise ValueError("media link not bound in interactive representation "+rid+": "+link)
  elif link not in md_text or link not in html_text: raise ValueError("media link not bound in both outputs: "+link)
 if not groups or any(kinds!=set(KINDS) for kinds in groups.values()): raise ValueError("each sample requires 1:1 audio/waveform/spectrogram/playback")
 if not data.get("visual_evidence"): raise ValueError("visual evidence required")
 for row in data["visual_evidence"]: check_file(root,row)
 if has_bundle:
  for members,order in eq_groups:
   for rid in members:
    if reps[rid][3]!=order: raise ValueError("equivalence group member must declare the group section order: "+rid)
    if title not in reps[rid][1]: raise ValueError("equivalence group member missing the shared title: "+rid)
  if len(canon_ids)>1 and not any(canon_ids<=members for members,_ in eq_groups): raise ValueError("multiple canonical representations require one declared equivalence group")
 return {"samples":len(groups),"media":sum(map(len,groups.values())),"bundle_classification":"declared" if has_bundle else "legacy/unspecified"}
def main():
 p=argparse.ArgumentParser(); p.add_argument("manifest"); p.add_argument("--classification",action="store_true"); a=p.parse_args(); result=verify(a.manifest)
 if a.classification: print(result["bundle_classification"])
 else:
  if result["bundle_classification"]=="legacy/unspecified": result.pop("bundle_classification")
  print(json.dumps(result,sort_keys=True))
if __name__=="__main__":
 try: main()
 except (ValueError,KeyError,TypeError,AttributeError,json.JSONDecodeError) as e: print("report-manifest-verify:",e,file=sys.stderr); raise SystemExit(65)
