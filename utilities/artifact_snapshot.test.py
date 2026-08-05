#!/usr/bin/env python3
import json, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HELPER=ROOT/"utilities/artifact-snapshot.py"


class ArtifactSnapshotTest(unittest.TestCase):
 def route(self, root: Path, *, route_id="rt-one", capability="autopilot-refine", intensity="standard") -> Path:
  path=root/f"{route_id}.json"
  path.write_text(json.dumps({"route_id":route_id,"route_hash":f"sha256:{route_id}","capability":capability,"effective_intensity":intensity,"nodes":[{"id":"transaction","write_scope":["target-artifact"]}]}))
  return path

 def run_helper(self, artifact: Path, target: Path, route: Path, route_id: str):
  return subprocess.run([sys.executable,str(HELPER),"prepare","--artifact-root",str(artifact),"--target",str(target),"--route",str(route),"--route-id",route_id,"--node","transaction"],text=True,capture_output=True)

 def test_same_route_reuses_one_version_and_preserves_relative_paths(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); artifact=root/".agent_reports"; doc=artifact/"documents/cycle/doc.md"; appendix=artifact/"documents/cycle/parts/appendix.md"
   appendix.parent.mkdir(parents=True); doc.write_text("doc-before\n"); appendix.write_text("appendix-before\n")
   route=self.route(root)
   first=self.run_helper(artifact,doc,route,"rt-one"); second=self.run_helper(artifact,appendix,route,"rt-one"); repeat=self.run_helper(artifact,doc,route,"rt-one")
   self.assertEqual((first.returncode,second.returncode,repeat.returncode),(0,0,0),first.stderr+second.stderr+repeat.stderr)
   version=artifact/"documents/cycle/_internal/versions/v1"
   self.assertEqual((version/"doc.md").read_text(),"doc-before\n")
   self.assertEqual((version/"parts/appendix.md").read_text(),"appendix-before\n")
   self.assertEqual(len(list((version.parent).glob("v*"))),1)
   self.assertEqual(json.loads(repeat.stdout)["snapshot"],"matched")

 def test_next_route_allocates_next_version(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); artifact=root/".agent_reports"; doc=artifact/"research/topic/report.md"; doc.parent.mkdir(parents=True); doc.write_text("v0\n")
   one=self.route(root,route_id="rt-one"); self.assertEqual(self.run_helper(artifact,doc,one,"rt-one").returncode,0)
   doc.write_text("v1\n"); two=self.route(root,route_id="rt-two"); self.assertEqual(self.run_helper(artifact,doc,two,"rt-two").returncode,0)
   self.assertEqual((doc.parent/"_internal/versions/v1/report.md").read_text(),"v0\n")
   self.assertEqual((doc.parent/"_internal/versions/v2/report.md").read_text(),"v1\n")

 def test_direct_refine_and_new_target_do_not_snapshot(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); artifact=root/".agent_reports"; doc=artifact/"documents/cycle/doc.md"; doc.parent.mkdir(parents=True); doc.write_text("before\n")
   direct=self.route(root,intensity="direct"); result=self.run_helper(artifact,doc,direct,"rt-one")
   self.assertEqual(result.returncode,0,result.stderr); self.assertIn("minor-direct-edit",result.stdout); self.assertFalse((doc.parent/"_internal").exists())
   major=self.route(root,route_id="rt-two"); new=doc.parent/"new.md"; result=self.run_helper(artifact,new,major,"rt-two")
   self.assertEqual(result.returncode,0,result.stderr); self.assertIn("new-target",result.stdout); self.assertFalse((doc.parent/"_internal").exists())

 def test_draft_refinement_snapshots_existing_file(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); artifact=root/".agent_reports"; draft=artifact/"documents/cycle/draft/manuscript.md"; draft.parent.mkdir(parents=True); draft.write_text("draft\n")
   route=self.route(root,capability="autopilot-draft",intensity="direct"); result=self.run_helper(artifact,draft,route,"rt-one")
   self.assertEqual(result.returncode,0,result.stderr)
   self.assertEqual((artifact/"documents/cycle/_internal/versions/v1/draft/manuscript.md").read_text(),"draft\n")

 def test_unowned_container_and_mismatched_preimage_fail_closed(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); artifact=root/".agent_reports"; legacy=artifact/"rebuttal/rebuttal.md"; legacy.parent.mkdir(parents=True); legacy.write_text("legacy\n")
   route=self.route(root); result=self.run_helper(artifact,legacy,route,"rt-one")
   self.assertEqual(result.returncode,65); self.assertIn("target-container-unowned",result.stderr)
   doc=artifact/"documents/cycle/doc.md"; doc.parent.mkdir(parents=True); doc.write_text("before\n")
   self.assertEqual(self.run_helper(artifact,doc,route,"rt-one").returncode,0)
   snapshot=doc.parent/"_internal/versions/v1/doc.md"; snapshot.write_text("corrupt\n")
   result=self.run_helper(artifact,doc,route,"rt-one")
   self.assertEqual(result.returncode,65); self.assertIn("snapshot-preimage-mismatch",result.stderr)

 def test_existing_legacy_sibling_layout_is_preserved(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); artifact=root/".agent_reports"; doc=artifact/"documents/legacy/doc.md"; doc.parent.mkdir(parents=True); doc.write_text("current\n"); (doc.parent/"doc_v1.md").write_text("old\n")
   route=self.route(root); result=self.run_helper(artifact,doc,route,"rt-one")
   self.assertEqual(result.returncode,0,result.stderr)
   self.assertEqual((doc.parent/"doc_v2.md").read_text(),"current\n")
   self.assertFalse((doc.parent/"_internal").exists())


if __name__=="__main__": unittest.main()
