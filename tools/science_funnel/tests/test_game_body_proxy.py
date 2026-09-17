import unittest
from unittest.mock import patch, MagicMock
from tools.game_shell.server import Handler
class ProxyRouting(unittest.TestCase):
 def test_private_engine_owns_reads_and_writes(self):
  handler=object.__new__(Handler);handler.engine_url='http://127.0.0.1:8123';handler._send=MagicMock();handler._json=MagicMock()
  for route,method,body in [('/tick_state','GET',None),('/verts','GET',None),('/tick_pose','POST',b'{"joint_index":13,"deg":20}')]:
   with self.subTest(route=route),patch('tools.game_shell.server.urllib.request.urlopen') as open_url:
    response=open_url.return_value.__enter__.return_value;response.read.return_value=b'{}';response.headers.get.return_value='application/json'
    handler._proxy(route,method,body)
    req=open_url.call_args.args[0]
    self.assertEqual(req.full_url,handler.engine_url+route);self.assertEqual(req.method,method);self.assertEqual(req.data,body)
    handler._json.assert_not_called()
if __name__=='__main__':unittest.main()
