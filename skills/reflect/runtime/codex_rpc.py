"""Stdio transport adapted from the retained Reflect RPC runner; no import side effects."""
from collections import deque
import json
import os
from pathlib import Path
import queue
import subprocess
import threading
import time

from evaluation import EvaluationError


class RPC:
    def __init__(self, command, workspace, *, environment=None, stop=None):
        self.queue = queue.Queue(); self.pending = deque(); self.sequence = 0
        self.stop = stop
        self.closed = False
        self.events = self._open(workspace / "events.jsonl")
        self.requests = self._open(workspace / "requests.jsonl")
        self.errors = self._open(workspace / "transport.stderr.log")
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.errors, text=True, bufsize=1, env=environment)
        self.reader = threading.Thread(target=self._read, daemon=True); self.reader.start()

    @staticmethod
    def _open(path):
        stream = Path(path).open("x"); Path(path).chmod(0o600); return stream

    def _read(self):
        try:
            for line in self.process.stdout:
                try:
                    message = json.loads(line)
                    if not isinstance(message, dict):
                        raise ValueError()
                except ValueError:
                    message = {"_invalid_transport_line": True}
                self.events.write(json.dumps(message, ensure_ascii=False) + "\n"); self.events.flush()
                self.queue.put(message)
        finally:
            self.queue.put({"_eof": True})

    def send(self, method, params=None, *, request=True):
        value = {"method": method, "params": params or {}}
        if request:
            self.sequence += 1; value["id"] = self.sequence
        body = json.dumps(value)
        self.requests.write(body + "\n"); self.requests.flush()
        self.process.stdin.write(body + "\n"); self.process.stdin.flush()
        return value.get("id")

    def call(self, method, params=None, *, timeout=15):
        identity = self.send(method, params)
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            try:
                message = self.queue.get(timeout=max(0.001, end - time.monotonic()))
            except queue.Empty:
                break
            if message.get("_eof"):
                raise EvaluationError("app-server-exited")
            if message.get("id") == identity and "method" not in message:
                if "error" in message:
                    raise EvaluationError("app-server-request-rejected")
                return message.get("result")
            self.pending.append(message)
        raise TimeoutError()

    def next(self, timeout):
        return self.pending.popleft() if self.pending else self.queue.get(timeout=timeout)

    def close(self):
        failure = None
        try:
            self.process.stdin.close()
        except BrokenPipeError:
            pass
        if self.process.poll() is None:
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                if self.stop:
                    try:
                        self.stop()
                    except Exception as error:
                        failure = error
                self.process.terminate()
                try:
                    self.process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.process.kill(); self.process.wait()
        self.reader.join(timeout=3)
        if self.reader.is_alive():
            raise EvaluationError("transport-reader-still-active")
        self.process.stdout.close()
        for stream in (self.events, self.requests, self.errors):
            stream.close()
        self.closed = True
        if failure:
            raise failure
