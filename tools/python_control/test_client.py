import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from .client import EngineControl, NativeRefusal
from .__main__ import run_scenario

class ControlContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.calls=[]
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args): pass
            def do_POST(self):
                data=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
                cls.calls.append((self.path,data))
                body=json.dumps({"ok":False,"error":"native admission refused"} if data.get("gamma")==999 else {"ok":True}).encode()
                self.send_response(200);self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
        cls.server=HTTPServer(("127.0.0.1",0),Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls): cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def setUp(self): self.engine=EngineControl(f"http://127.0.0.1:{self.server.server_port}");self.calls.clear()
    def tearDown(self): self.engine.close()
    def test_native_refusal_is_not_http_success(self):
        with self.assertRaises(NativeRefusal):self.engine.membrane.tension(999)
        self.assertEqual(len(self.calls),1) # Mutating failures are never retried.
    def test_nonfinite_values_cannot_reach_native_parser(self):
        for value in [float("nan"),float("inf"),True]:
            with self.assertRaises(ValueError):self.engine.membrane.tension(value)
        self.assertFalse(self.calls)
    def test_batch_uses_native_run_not_step_which_ignores_count(self):
        self.engine.membrane.step(12)
        self.assertEqual(self.calls,[('/membrane_demo',{'op':'run','n_steps':12})])
    def test_direct_pose_cannot_be_sent_as_physics_intent(self):
        with self.assertRaises(ValueError):self.engine.physics.intent(elbow_deg=0)
        self.assertFalse(self.calls)
    def test_scenario_typo_refused_before_first_mutation(self):
        with self.assertRaises(ValueError):run_scenario(self.engine,{'operations':[{'op':'reset'},{'op':'stepp'}]})
        self.assertFalse(self.calls)
    def test_explicit_local_engine_only(self):
        for url in ['http://example.com','http://127.0.0.1/path','https://localhost','http://x@localhost']:
            with self.assertRaises(ValueError):EngineControl(url)

if __name__=='__main__':unittest.main()
