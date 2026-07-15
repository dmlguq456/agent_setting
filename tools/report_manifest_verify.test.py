#!/usr/bin/env python3
import hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
P=Path(__file__).with_name("report-manifest-verify.py"); S=importlib.util.spec_from_file_location("report",P); V=importlib.util.module_from_spec(S); S.loader.exec_module(V)
class TestReport(unittest.TestCase):
 def fixture(self,root):
  names=["audio.wav","waveform.png","spectrogram.png","playback.html"]
  for n in names: (root/n).write_text(n)
  links=" ".join(names); (root/"REPORT.md").write_text("score 7 "+links); (root/"report.html").write_text("<p>score 7 "+links+"</p>")
  def row(n,kind=None): return {"path":n,"sha256":hashlib.sha256((root/n).read_bytes()).hexdigest(),**({"sample_id":"s1","kind":kind} if kind else {})}
  data={"schema_version":1,"outputs":{"markdown":row("REPORT.md"),"html":row("report.html")},"summary_stats":{"score":7},"house_parameters":{"sample_rate_hz":48000,"frequency_band_hz":[0,24000]},"media":[row(n,k) for n,k in zip(names,V.KINDS)],"visual_evidence":[row("waveform.png")]}
  p=root/"report_manifest.json"; p.write_text(json.dumps(data)); return p,data
 def test_valid_and_hash(self):
  with tempfile.TemporaryDirectory() as td:
   p,d=self.fixture(Path(td)); self.assertEqual(V.verify(p)["media"],4); Path(td,"audio.wav").write_text("changed"); self.assertRaises(ValueError,V.verify,p)
 def test_one_to_one(self):
  with tempfile.TemporaryDirectory() as td:
   p,d=self.fixture(Path(td)); d["media"].pop(); p.write_text(json.dumps(d)); self.assertRaises(ValueError,V.verify,p)
if __name__=="__main__": unittest.main()
