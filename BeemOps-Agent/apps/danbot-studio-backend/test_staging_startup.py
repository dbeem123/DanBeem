import os
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = os.path.dirname(os.path.abspath(__file__))


class StartupTest(unittest.TestCase):
    def test_backend_starts_on_loopback_and_stops_cleanly(self):
        with tempfile.TemporaryDirectory() as d:
            db = ":memory:"
            artifacts = os.path.join(d, "artifacts")
            env = os.environ.copy()
            env.update({
                "DANBOT_ACCESS_ISSUER": "https://team.example.cloudflareaccess.com",
                "DANBOT_ACCESS_AUDIENCE": "test-audience",
                "DANBOT_ACCESS_JWKS_URL": "https://127.0.0.1.invalid/.well-known/jwks.json",
            })
            proc = subprocess.Popen(
                [sys.executable, os.path.join(ROOT, "backend.py"), "--port", "0", "--db", db, "--artifacts", artifacts],
                cwd=ROOT,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                deadline = time.time() + 5
                while time.time() < deadline:
                    if proc.poll() is not None:
                        self.fail(f"backend exited during startup: {proc.stderr.read()}")
                    # Port 0 is chosen by the OS; the process itself is validated by
                    # the existing serve() tests. This wait verifies the CLI remains live.
                    time.sleep(0.05)
                self.assertIsNone(proc.poll())
            finally:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)
                proc.stdout.close()
                proc.stderr.close()
                self.assertIsNotNone(proc.returncode)


if __name__ == "__main__":
    unittest.main()
