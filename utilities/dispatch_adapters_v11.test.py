#!/usr/bin/env python3
import importlib.util, io, os, subprocess, sys, tempfile, threading, unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]

ADAPTERS={
 "codex":([sys.executable,str(ROOT/"adapters/codex/bin/dispatch-headless.py")],["--model","gpt-test","--reasoning","low"]),
 "claude":([sys.executable,str(ROOT/"adapters/claude/bin/dispatch-headless.py")],["--model","claude-test","--effort","low"]),
 "opencode":([sys.executable,str(ROOT/"adapters/opencode/bin/dispatch-headless.py")],["--model","provider/test","--variant","low"]),
}

class AdapterV11Test(unittest.TestCase):
 def load_wrapper(self,harness):
  spec=importlib.util.spec_from_file_location(f"{harness}_dispatch_fixture",ROOT/f"adapters/{harness}/bin/dispatch-headless.py")
  wrapper=importlib.util.module_from_spec(spec); spec.loader.exec_module(wrapper); return wrapper
 def fixture(self,root):
  repo=root/"repo"; repo.mkdir(); subprocess.run(["git","init","-q",str(repo)],check=True)
  subprocess.run(["git","-C",str(repo),"config","user.email","fixture@example.com"],check=True)
  subprocess.run(["git","-C",str(repo),"config","user.name","Fixture"],check=True)
  (repo/"x").write_text("x"); subprocess.run(["git","-C",str(repo),"add","x"],check=True); subprocess.run(["git","-C",str(repo),"commit","-qm","init"],check=True)
  art=root/".agent_reports"; art.mkdir(); return repo,art
 def command(self,harness,action,repo,jobs,logs,status="supported"):
  wrapper,model=ADAPTERS[harness]
  return wrapper+[f"--{action}","--worktree",str(repo),"--slug",f"{harness}-v11","--capability","autopilot-code","--mode","dev/backend","--intensity","standard","--dispatch-depth","2","--parent","owner","--worker-role","code-plan","--owner","autopilot-code","--jobs",str(jobs),"--log-dir",str(logs),"--attempt-id",f"att-{harness}-fixture-0001","--parent-harness",harness,"--parent-transport","headless","--parent-sandbox","fixture","--launch-authority","conductor","--nested-eligibility",status,"--eligibility-source",f"{harness}-fixture","--fallback-ordinal","1"]+model
 def test_sibling_registry_rows_and_nested_refusal(self):
  for harness in ADAPTERS:
   with self.subTest(harness=harness), tempfile.TemporaryDirectory() as td:
    root=Path(td); repo,art=self.fixture(root); jobs=root/"jobs.log"; logs=root/"logs"
    env={**os.environ,"AGENT_HOME":str(ROOT),"AGENT_ARTIFACT_ROOT":str(art),
         "AGENT_DISPATCH_JOBS":str(jobs),"OPENCODE_CONFIG_CONTENT":"{}"}
    registered=subprocess.run(self.command(harness,"register",repo,jobs,logs),text=True,capture_output=True,env=env)
    self.assertEqual(registered.returncode,0,registered.stdout+registered.stderr)
    row=jobs.read_text(encoding="utf-8")
    self.assertIn(f"harness={harness}",row); self.assertIn("attempt_id=att-",row)
    self.assertIn("nested_eligibility=supported",row); self.assertIn("fallback_ordinal=1",row)
    duplicate=subprocess.run(self.command(harness,"register",repo,jobs,logs),text=True,capture_output=True,env=env)
    self.assertEqual(duplicate.returncode,0,duplicate.stdout+duplicate.stderr)
    self.assertIn("duplicate_attempt=1",duplicate.stdout); self.assertIn("registered=0",duplicate.stdout)
    self.assertEqual(len(jobs.read_text(encoding="utf-8").splitlines()),1)
    denied=subprocess.run(self.command(harness,"start",repo,jobs,logs,status="unknown"),text=True,capture_output=True,env=env)
    self.assertEqual(denied.returncode,69,denied.stdout+denied.stderr)
    self.assertIn("reason=nested-child-spawn-unknown",denied.stdout)
    unwritable=Path("/proc/1/stage-dispatch-v11")/f"{harness}.jobs.log"
    blocked_env={**env}; blocked_env.pop("AGENT_DISPATCH_JOBS",None)
    blocked=subprocess.run(self.command(harness,"register",repo,unwritable,logs),text=True,capture_output=True,env=blocked_env)
    self.assertEqual(blocked.returncode,73,blocked.stdout+blocked.stderr)
    self.assertIn("reason=global-registry-unwritable",blocked.stdout)
    self.assertIn("child_spawned=0",blocked.stdout)
 def test_codex_owner_gets_scoped_nested_network_only_at_depth_one(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); repo,art=self.fixture(root); logs=root/"logs"
   claude_config=root/"claude"; (claude_config/"session-env").mkdir(parents=True)
   command=[sys.executable,str(ROOT/"adapters/codex/bin/dispatch-headless.py"),"--dry-run",
            "--worktree",str(repo),"--slug","codex-owner","--capability","autopilot-code",
            "--mode","dev/backend","--intensity","standard","--dispatch-depth","1","--worker-type","owner",
            "--model","gpt-test","--reasoning","low","--log-dir",str(logs)]
   env={**os.environ,"AGENT_HOME":str(ROOT),"AGENT_ARTIFACT_ROOT":str(art),
        "CLAUDE_CONFIG_DIR":str(claude_config)}
   result=subprocess.run(command,text=True,capture_output=True,env=env)
   self.assertEqual(result.returncode,0,result.stdout+result.stderr)
   self.assertIn("nested_headless_network=1",result.stdout)
   self.assertIn("sandbox_workspace_write.network_access=true",result.stdout)
   self.assertIn(f"--add-dir {ROOT / '.dispatch'}",result.stdout)
   self.assertIn(f"--add-dir {ROOT / '.core-grounding'}",result.stdout)
   self.assertIn(f"--add-dir {claude_config / 'session-env'}",result.stdout)
   self.assertIn("nested_owner_writable_dirs=",result.stdout)
   self.assertIn("nested_codex_home=",result.stdout)
   self.assertIn("broker_lifecycle=retired",result.stdout)
 def test_route_bound_depth_two_codex_gets_heartbeat_scope_without_network(self):
  spec=importlib.util.spec_from_file_location("codex_dispatch_scope",ROOT/"adapters/codex/bin/dispatch-headless.py")
  wrapper=importlib.util.module_from_spec(spec);spec.loader.exec_module(wrapper)
  args=type("Args",(),{
   "worktree":"/work/repo","artifact_root":"/artifacts","nested_headless_network":False,
   "agent_home":ROOT,"dispatch_depth":2,"route_id":"rt-1","attempt_id":"att-stage-1",
   "sandbox":"workspace-write","resolved_model_settings":{"source":"inherit"},"approval":"inherit"})()
  command=wrapper.shell_command(args,Path("/prompt"),Path("/log"))
  self.assertIn(f"--add-dir {ROOT / '.dispatch'}",command)
  self.assertNotIn("network_access=true",command)
 def test_foreground_codex_child_reuses_checked_outer_sandbox(self):
  wrapper=self.load_wrapper("codex")
  args=type("Args",(),{
   "worktree":"/work/repo","artifact_root":"/artifacts","nested_headless_network":False,
   "agent_home":ROOT,"dispatch_depth":2,"route_id":"rt-1","attempt_id":"att-stage-1",
   "sandbox":"workspace-write","launch_lifecycle":"foreground-scoped",
   "parent_harness":"codex","parent_transport":"headless","parent_sandbox":"workspace-write",
   "resolved_model_settings":{"source":"inherit"},"approval":"inherit"})()
  with mock.patch.dict(os.environ,{"AGENT_DISPATCH_CHILD":"1"},clear=False):
   command=wrapper.shell_command(args,Path("/prompt"),Path("/log"))
   self.assertEqual(wrapper.effective_runtime_sandbox(args),"danger-full-access")
  self.assertIn("--sandbox danger-full-access",command)
 def test_background_governor_does_not_hold_orchestrator_capture_pipes(self):
  for harness in ADAPTERS:
   with self.subTest(harness=harness):
    source=(ROOT/f"adapters/{harness}/bin/dispatch-headless.py").read_text(encoding="utf-8")
    start=source.index("proc = subprocess.Popen")
    end=source.index("except OSError",start)
    launch=source[start:end]
    self.assertIn("stdin=subprocess.DEVNULL",launch)
    self.assertIn("stdout=subprocess.DEVNULL",launch)
    self.assertIn("stderr=subprocess.DEVNULL",launch)
    self.assertIn('pid_scope=namespace-local',source)
    self.assertIn('os.environ.get("AGENT_DISPATCH_CHILD") == "1"',source)
 def test_nested_codex_home_links_auth_but_keeps_mutable_state_local(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); source=root/"source"; source.mkdir(); worktree=root/"worktree"; worktree.mkdir()
   (source/"auth.json").write_text("{}\n",encoding="utf-8")
   (source/"config.toml").write_text("model = \"fixture\"\n",encoding="utf-8")
   spec=importlib.util.spec_from_file_location("codex_dispatch_home",ROOT/"adapters/codex/bin/dispatch-headless.py")
   wrapper=importlib.util.module_from_spec(spec); spec.loader.exec_module(wrapper)
   home=wrapper.prepare_nested_codex_home(worktree,source)
   self.assertTrue((home/"auth.json").is_symlink())
   self.assertEqual((home/"auth.json").resolve(),(source/"auth.json").resolve())
   self.assertTrue((home/"config.toml").is_symlink())
   self.assertTrue((home/"agent-harness").is_symlink())
   self.assertEqual((home/"agent-harness").resolve(),wrapper.resolve_agent_home().resolve())
   self.assertEqual(home.parent,worktree/".dispatch")
 def test_foreground_scoped_completion_is_recorded_for_codex_and_claude(self):
  for harness in ("codex","claude"):
   with self.subTest(harness=harness), tempfile.TemporaryDirectory() as td:
    root=Path(td); repo,art=self.fixture(root); jobs=root/"jobs.log"; logs=root/"logs"; fakebin=root/"bin"; fakebin.mkdir()
    fake=fakebin/harness; fake.write_text("#!/bin/sh\nexit 0\n",encoding="utf-8"); fake.chmod(0o755)
    command=self.command(harness,"start",repo,jobs,logs)+["--launch-lifecycle","foreground-scoped","--foreground-timeout","2"]
    wrapper=self.load_wrapper(harness); argv=["dispatch-headless.py",*command[2:]]
    env={**os.environ,"PATH":str(fakebin)+os.pathsep+os.environ.get("PATH",""),"AGENT_HOME":str(ROOT),"AGENT_ARTIFACT_ROOT":str(art),"AGENT_DISPATCH_JOBS":str(jobs),"AGENT_DISPATCH_CHILD":"1"}
    stream=io.StringIO()
    patches=[mock.patch.dict(os.environ,env,clear=True)]
    if hasattr(wrapper,"check_runtime_projection"): patches.append(mock.patch.object(wrapper,"check_runtime_projection",return_value=0))
    if hasattr(wrapper,"ensure_runtime_home_projection"): patches.append(mock.patch.object(wrapper,"ensure_runtime_home_projection",return_value=None))
    for patch in patches: patch.start()
    try:
     with redirect_stdout(stream): code=wrapper.main(argv)
    finally:
     for patch in reversed(patches): patch.stop()
    self.assertEqual(code,0,stream.getvalue())
    self.assertIn("launch_lifecycle=foreground-scoped",stream.getvalue())
    self.assertIn("worker_exit=0",stream.getvalue())
    self.assertIn("worker_failure=-",stream.getvalue())
    row=jobs.read_text(encoding="utf-8")
    self.assertIn("launch_lifecycle=foreground-scoped",row)
    self.assertIn("\topen\t",row)
 def test_exact_attempt_row_closure_is_isolated_for_both_wrappers(self):
  for harness in ("codex","claude"):
   with self.subTest(harness=harness), tempfile.TemporaryDirectory() as td:
    jobs=Path(td)/"jobs.log"; worktree="/fixture/worktree"; slug="stage"
    contract=("attempt_schema_version=2,dispatch_depth=2,transport=headless,"
              "execution_surface=registered-headless,registered_worker=1,"
              "fallback_hop=same-harness-headless")
    jobs.write_text(
     f"2026-07-20T00:00:00Z\topen\t/repo\t{worktree}\t{slug}\t{contract},attempt_id=att-a\n"
     f"2026-07-20T00:00:01Z\topen\t/repo\t{worktree}\t{slug}\t{contract},attempt_id=att-b\n",encoding="utf-8")
    wrapper=self.load_wrapper(harness)
    self.assertTrue(wrapper.close_job_row(jobs,slug,worktree,"timeout","","att-a"))
    rows=jobs.read_text(encoding="utf-8").splitlines()
    self.assertIn("\tdone\t",rows[0]); self.assertIn("note=dead-timeout",rows[0])
    self.assertIn("\topen\t",rows[1]); self.assertNotIn("note=",rows[1])
 def test_concurrent_codex_start_launches_exactly_one_child(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); repo,art=self.fixture(root); jobs=root/"jobs.log"; logs=root/"logs"
   fakebin=root/"bin"; fakebin.mkdir(); count=root/"child-count"
   fake=fakebin/"codex"
   fake.write_text("#!/bin/sh\nprintf 'child\\n' >> \"$FAKE_CHILD_COUNT\"\n",encoding="utf-8")
   fake.chmod(0o755)
   command=self.command("codex","start",repo,jobs,logs)
   spec=importlib.util.spec_from_file_location("codex_dispatch_concurrency",ROOT/"adapters/codex/bin/dispatch-headless.py")
   wrapper=importlib.util.module_from_spec(spec); spec.loader.exec_module(wrapper)
   argv=["dispatch-headless.py",*command[2:]]
   env={**os.environ,"PATH":str(fakebin)+os.pathsep+os.environ.get("PATH",""),
        "AGENT_HOME":str(ROOT),"AGENT_ARTIFACT_ROOT":str(art),
        "AGENT_DISPATCH_JOBS":str(jobs),"AGENT_DISPATCH_CHILD":"1",
        "AGENT_DISPATCH_ALLOW_NAMESPACED_SPAWN":"1",
        "FAKE_CHILD_COUNT":str(count)}
   codes=[]
   def invoke(): codes.append(wrapper.main(argv))
   with mock.patch.dict(os.environ,env,clear=True), \
        mock.patch.object(wrapper,"check_runtime_projection",return_value=0), \
        mock.patch.object(wrapper,"ensure_runtime_home_projection",return_value=None):
    threads=[threading.Thread(target=invoke) for _ in range(2)]
    for thread in threads: thread.start()
    for thread in threads: thread.join(timeout=20)
   self.assertEqual(sorted(codes),[0,0],codes)
   for _ in range(50):
    if count.exists(): break
    import time; time.sleep(.02)
   self.assertTrue(count.is_file(),codes)
   self.assertEqual(count.read_text(encoding="utf-8").splitlines(),["child"])
   self.assertEqual(len(jobs.read_text(encoding="utf-8").splitlines()),1)
   self.assertIn("launch_claimed=1",jobs.read_text(encoding="utf-8"))
   self.assertIn("pid_scope=namespace-local",jobs.read_text(encoding="utf-8"))
   self.assertIn("launch_lifecycle=detached",jobs.read_text(encoding="utf-8"))

if __name__=="__main__": unittest.main()
