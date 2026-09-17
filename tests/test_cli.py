"""Run the real entry point with a duplex pipe and inspect durable results."""

from __future__ import annotations

import json
import os
import queue
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path


class TerminalTests(unittest.TestCase):
    def test_two_way_conversation_and_process_restart(self) -> None:
        root = Path(__file__).resolve().parents[1]
        env = {**os.environ, "PYTHONPATH": str(root / "src")}
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / "conversation.sqlite3"
            command = [sys.executable, "-m", "enthus", "--mode", "offline", "--database", str(database)]
            process = subprocess.Popen(command, cwd=root, env=env, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            lines: queue.Queue[str] = queue.Queue()
            transcript: list[str] = []

            def collect() -> None:
                for line in process.stdout:
                    lines.put(line)

            reader = threading.Thread(target=collect, daemon=True)
            reader.start()

            def wait_for(fragment: str) -> None:
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline:
                    try:
                        line = lines.get(timeout=0.1)
                    except queue.Empty:
                        continue
                    transcript.append(line)
                    if fragment in line:
                        return
                self.fail(f"Missing {fragment!r}: {''.join(transcript)}")

            try:
                wait_for("OFFLINE DIAGNOSTIC")
                process.stdin.write("I am making a game.\n")
                process.stdin.flush()
                wait_for("Recent context contains 1 messages.")
                process.stdin.write("/mute\nA small puzzle game.\n")
                process.stdin.flush()
                wait_for("Recent context contains 3 messages.")
                process.stdin.close()
                self.assertEqual(process.wait(timeout=10), 0)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
                if not process.stdin.closed:
                    process.stdin.close()
                reader.join(timeout=2)
                process.stdout.close()
            restarted = subprocess.run(command, input="Continue that game.\n", capture_output=True,
                                       text=True, env=env, cwd=root, timeout=10)
            self.assertEqual(restarted.returncode, 0, restarted.stderr)
            self.assertIn("Recent context contains 5 messages.", restarted.stdout)
            with sqlite3.connect(database) as db:
                state = json.loads(db.execute("SELECT data FROM state").fetchone()[0])
                self.assertEqual(state["remaining_calls"], 97)
                self.assertEqual(state["mute_until"], -1)
                self.assertEqual(db.execute("SELECT count(*) FROM messages").fetchone()[0], 6)


if __name__ == "__main__":
    unittest.main()
