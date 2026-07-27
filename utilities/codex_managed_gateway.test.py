#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import queue
import socket
import sys
import tempfile
import threading
import time
import unittest
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "codex_managed_gateway",
    ROOT / "utilities" / "codex-managed-gateway.py",
)
assert SPEC and SPEC.loader
GATEWAY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GATEWAY
SPEC.loader.exec_module(GATEWAY)


def wait_path(path: Path, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return
        time.sleep(0.01)
    raise AssertionError(f"socket did not appear: {path}")


class RpcClient:
    def __init__(self, path: Path) -> None:
        self.websocket = GATEWAY.WebSocket.connect_unix(path)
        self._next_id = 1
        self._pending: dict[tuple[str, Any], queue.Queue[dict[str, Any]]] = {}
        self._messages: list[dict[str, Any]] = []
        self._cv = threading.Condition()
        self._closed = False
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

    def _read_loop(self) -> None:
        try:
            while True:
                value = self.websocket.read_json()
                key = GATEWAY.request_key(value.get("id"))
                with self._cv:
                    if (
                        key in self._pending
                        and ("result" in value or "error" in value)
                    ):
                        self._pending[key].put(value)
                    self._messages.append(value)
                    self._cv.notify_all()
        except (EOFError, OSError, GATEWAY.GatewayError):
            pass
        finally:
            with self._cv:
                self._closed = True
                self._cv.notify_all()

    def request(
        self,
        method: str,
        params: dict[str, Any],
        timeout: float = 5.0,
    ) -> dict[str, Any]:
        request_id = self._next_id
        self._next_id += 1
        key = GATEWAY.request_key(request_id)
        assert key is not None
        response_queue: queue.Queue[dict[str, Any]] = queue.Queue(maxsize=1)
        with self._cv:
            self._pending[key] = response_queue
        self.websocket.write_json(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": params,
            }
        )
        try:
            response = response_queue.get(timeout=timeout)
        finally:
            with self._cv:
                self._pending.pop(key, None)
        if "error" in response:
            raise AssertionError(f"{method} failed: {response['error']}")
        return response["result"]

    def notify(self, method: str, params: dict[str, Any]) -> None:
        self.websocket.write_json(
            {"jsonrpc": "2.0", "method": method, "params": params}
        )

    def respond(self, request_id: Any, result: dict[str, Any]) -> None:
        self.websocket.write_json(
            {"jsonrpc": "2.0", "id": request_id, "result": result}
        )

    def wait_for(
        self,
        predicate: Callable[[dict[str, Any]], bool],
        timeout: float = 5.0,
    ) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        with self._cv:
            while True:
                for value in self._messages:
                    if predicate(value):
                        return value
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise AssertionError("message wait timed out")
                if self._closed:
                    raise AssertionError("client closed while waiting")
                self._cv.wait(min(remaining, 0.1))

    def close(self) -> None:
        self.websocket.close()
        self._reader.join(timeout=2)


class FakeAppServer:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.listener.bind(str(path))
        self.listener.listen(4)
        self.stop = threading.Event()
        self.lock = threading.Lock()
        self.messages: list[dict[str, Any]] = []
        self.connections = 0
        self.start_count = 0
        self.steer_count = 0
        self.approval_responses: list[dict[str, Any]] = []
        self.hold_start = False
        self.start_received = threading.Event()
        self.release_start = threading.Event()
        self.current: Any = None
        self.thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.thread.start()

    def _accept_loop(self) -> None:
        while not self.stop.is_set():
            try:
                connection, _ = self.listener.accept()
            except OSError:
                return
            with self.lock:
                self.connections += 1
            try:
                websocket = GATEWAY.WebSocket.accept(connection)
                self.current = websocket
                self._serve(websocket)
            except (EOFError, OSError, GATEWAY.GatewayError):
                pass
            finally:
                self.current = None
                try:
                    websocket.close()
                except (NameError, OSError):
                    connection.close()

    def _serve(self, websocket: Any) -> None:
        while not self.stop.is_set():
            message = websocket.read_json()
            with self.lock:
                self.messages.append(message)
            method = message.get("method")
            if method == "initialize":
                websocket.write_json(
                    {
                        "jsonrpc": "2.0",
                        "id": message["id"],
                        "result": {"serverInfo": {"name": "fake"}},
                    }
                )
            elif method == "initialized":
                continue
            elif method in {"thread/start", "thread/resume"}:
                websocket.write_json(
                    {
                        "jsonrpc": "2.0",
                        "id": message["id"],
                        "result": {"thread": {"id": "thread-1"}},
                    }
                )
            elif method == "turn/start":
                with self.lock:
                    self.start_count += 1
                    ordinal = self.start_count
                self.start_received.set()
                if self.hold_start:
                    self.release_start.wait(5)
                turn = {
                    "id": f"turn-{ordinal}",
                    "items": [],
                    "status": "inProgress",
                }
                websocket.write_json(
                    {
                        "jsonrpc": "2.0",
                        "id": message["id"],
                        "result": {"turn": turn},
                    }
                )
                websocket.write_json(
                    {
                        "jsonrpc": "2.0",
                        "method": "turn/started",
                        "params": {"threadId": "thread-1", "turn": turn},
                    }
                )
            elif method == "turn/steer":
                with self.lock:
                    self.steer_count += 1
                websocket.write_json(
                    {
                        "jsonrpc": "2.0",
                        "id": message["id"],
                        "result": {
                            "turnId": message["params"]["expectedTurnId"]
                        },
                    }
                )
            elif "id" in message and (
                "result" in message or "error" in message
            ):
                with self.lock:
                    self.approval_responses.append(message)
            elif "id" in message:
                websocket.write_json(
                    {
                        "jsonrpc": "2.0",
                        "id": message["id"],
                        "result": {},
                    }
                )

    def emit_approval(self) -> None:
        deadline = time.monotonic() + 5
        while self.current is None and time.monotonic() < deadline:
            time.sleep(0.01)
        if self.current is None:
            raise AssertionError("no upstream client")
        self.current.write_json(
            {
                "jsonrpc": "2.0",
                "id": 900,
                "method": "item/commandExecution/requestApproval",
                "params": {
                    "threadId": "thread-1",
                    "turnId": "turn-approval",
                    "itemId": "item-approval",
                    "reason": "fixture",
                },
            }
        )

    def counts(self) -> tuple[int, int]:
        with self.lock:
            return self.start_count, self.steer_count

    def methods(self) -> list[str]:
        with self.lock:
            return [
                str(value.get("method"))
                for value in self.messages
                if value.get("method")
            ]

    def close(self) -> None:
        self.stop.set()
        if self.current is not None:
            self.current.close()
        self.listener.close()
        self.thread.join(timeout=2)


def control(path: Path, value: dict[str, Any]) -> dict[str, Any]:
    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    connection.settimeout(10)
    connection.connect(str(path))
    connection.sendall((GATEWAY.canonical(value) + "\n").encode())
    data = bytearray()
    while b"\n" not in data:
        chunk = connection.recv(4096)
        if not chunk:
            break
        data.extend(chunk)
    connection.close()
    return json.loads(bytes(data).split(b"\n", 1)[0])


def receipt_request(batch: str = "batch-1") -> dict[str, Any]:
    return {
        "schema_version": 1,
        "op": "deliver",
        "thread_id": "thread-1",
        "parent_attempt_id": "att-parent",
        "sealed_batch_id": batch,
        "receipt": {
            "schema_version": 1,
            "state": "ready",
            "parent_attempt_id": "att-parent",
            "children": [
                {
                    "attempt_id": f"att-{batch}",
                    "status": "done",
                    "readiness": "ready",
                    "reason": "registry-closed",
                    "harness": "codex",
                }
            ],
        },
    }


class ManagedGatewayTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.upstream = self.root / "upstream.sock"
        self.front = self.root / "front.sock"
        self.control = self.root / "control.sock"
        self.ledger = self.root / "ledger.json"
        self.trace = self.root / "trace.jsonl"
        self.server = FakeAppServer(self.upstream)
        self.gateway = GATEWAY.ManagedGateway(
            listen_path=self.front,
            upstream_path=self.upstream,
            control_path=self.control,
            ledger_path=self.ledger,
            trace_path=self.trace,
        )
        self.gateway_thread = threading.Thread(
            target=self.gateway.serve_forever, daemon=True
        )
        self.gateway_thread.start()
        wait_path(self.front)
        wait_path(self.control)
        self.client = self._connect_client()

    def _connect_client(self) -> RpcClient:
        client = RpcClient(self.front)
        client.request(
            "initialize",
            {
                "clientInfo": {
                    "name": "managed-gateway-test",
                    "version": "1",
                },
                "capabilities": {"experimentalApi": True},
            },
        )
        client.notify("initialized", {})
        client.request("thread/start", {})
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            status = control(
                self.control,
                {"schema_version": 1, "op": "status"},
            )
            if status.get("thread_id") == "thread-1":
                return client
            time.sleep(0.01)
        raise AssertionError("gateway did not learn thread")

    def tearDown(self) -> None:
        self.client.close()
        self.gateway.close()
        self.server.close()
        self.gateway_thread.join(timeout=2)

    def test_idle_completion_starts_once_and_duplicate_replays(self) -> None:
        first = control(self.control, receipt_request())
        second = control(self.control, receipt_request())
        self.assertEqual(first["status"], "accepted")
        self.assertEqual(first["action"], "start")
        self.assertFalse(first["replay"])
        self.assertEqual(second["status"], "accepted")
        self.assertTrue(second["replay"])
        self.assertEqual(self.server.counts(), (1, 0))
        starts = [
            value for value in self.server.messages
            if value.get("method") == "turn/start"
        ]
        self.assertEqual(starts[0]["params"]["input"], [])
        encoded = GATEWAY.canonical(starts[0])
        self.assertIn("AGENT_HARNESS_COMPLETION_V1", encoded)
        self.assertNotIn("RAW_CHILD", encoded)

    def test_active_manual_turn_receipt_steers_without_second_turn(self) -> None:
        self.client.request(
            "turn/start",
            {
                "threadId": "thread-1",
                "input": [{"type": "text", "text": "manual"}],
            },
        )
        result = control(self.control, receipt_request())
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["action"], "steer")
        self.assertEqual(self.server.counts(), (1, 1))
        steer = next(
            value for value in self.server.messages
            if value.get("method") == "turn/steer"
        )
        self.assertEqual(steer["params"]["expectedTurnId"], "turn-1")
        self.assertEqual(steer["params"]["input"], [])

    def test_pending_start_race_is_one_start_plus_one_steer(self) -> None:
        self.server.hold_start = True
        barrier = threading.Barrier(3)
        outcomes: dict[str, Any] = {}

        def manual() -> None:
            barrier.wait()
            outcomes["manual"] = self.client.request(
                "turn/start",
                {
                    "threadId": "thread-1",
                    "input": [{"type": "text", "text": "race-manual"}],
                },
            )

        def completion() -> None:
            barrier.wait()
            outcomes["completion"] = control(
                self.control, receipt_request()
            )

        threads = [
            threading.Thread(target=manual),
            threading.Thread(target=completion),
        ]
        for thread in threads:
            thread.start()
        barrier.wait()
        self.assertTrue(self.server.start_received.wait(5))
        time.sleep(0.05)
        self.assertEqual(self.server.counts(), (1, 0))
        self.server.release_start.set()
        for thread in threads:
            thread.join(timeout=5)
            self.assertFalse(thread.is_alive())
        self.assertEqual(outcomes["completion"]["status"], "accepted")
        self.assertEqual(self.server.counts(), (1, 1))
        self.assertEqual(outcomes["manual"]["turn"]["id"], "turn-1")

    def test_approval_only_reaches_tui(self) -> None:
        self.server.emit_approval()
        request = self.client.wait_for(
            lambda value: (
                value.get("method")
                == "item/commandExecution/requestApproval"
            )
        )
        self.client.respond(request["id"], {"decision": "accept"})
        deadline = time.monotonic() + 5
        while (
            not self.server.approval_responses
            and time.monotonic() < deadline
        ):
            time.sleep(0.01)
        self.assertEqual(len(self.server.approval_responses), 1)
        status = control(
            self.control, {"schema_version": 1, "op": "status"}
        )
        self.assertEqual(status["approval_owner"], "tui")
        self.assertEqual(status["upstream_clients"], 1)
        self.assertNotIn(
            "requestApproval",
            self.trace.read_text(encoding="utf-8"),
        )

    def test_foreign_or_incomplete_receipt_never_reaches_upstream(self) -> None:
        before = self.server.counts()
        foreign = receipt_request()
        foreign["thread_id"] = "thread-foreign"
        result = control(self.control, foreign)
        self.assertEqual(result["status"], "rejected")
        incomplete = receipt_request("batch-incomplete")
        incomplete["receipt"]["children"][0]["readiness"] = "pending"
        result = control(self.control, incomplete)
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(self.server.counts(), before)

    def test_disconnect_fails_closed_then_reconnects(self) -> None:
        self.client.close()
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            status = control(
                self.control,
                {"schema_version": 1, "op": "status"},
            )
            if status["status"] == "disconnected":
                break
            time.sleep(0.01)
        result = control(self.control, receipt_request("batch-offline"))
        self.assertEqual(result["status"], "retryable")
        self.client = self._connect_client()
        result = control(self.control, receipt_request("batch-reconnected"))
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(self.server.connections, 2)


if __name__ == "__main__":
    unittest.main()
