import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from test_visual_capture import fixture
from visual_gate import verify

class Tests(unittest.TestCase):
    def test_files_and_camera_fail_closed(self):
        m,ctx,p=fixture(True)
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);media=root/'capture.bin';media.write_bytes(b'synthetic media identity only')
            ctx['capture_sha256']=hashlib.sha256(media.read_bytes()).hexdigest()
            m['capture_sha256']=ctx['capture_sha256'];camera=root/'camera.json'
            contract={'task_id':ctx['task_id'],'task':{'verification_profile':p}}
            receipt={'capture_context':ctx,'evidence':{'visual':{'reference':str(media),'raw_sha256':ctx['capture_sha256']},'camera':{'reference':str(camera)}}}
            def save():
                camera.write_text(json.dumps(m),encoding='utf-8')
                receipt['evidence']['camera']['raw_sha256']=hashlib.sha256(camera.read_bytes()).hexdigest()
            save();self.assertTrue(verify(receipt,contract)['structurally_valid'])
            self.assertFalse(verify(receipt,contract)['visual_acceptance'])
            good=copy.deepcopy(m)
            m['views'][0]['camera']['samples'][0]['distance_to_target']=100
            save()
            with self.assertRaisesRegex(ValueError,'distance_mismatch'):verify(receipt,contract)
            m=good;save();media.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'hash_mismatch'):verify(receipt,contract)

if __name__=='__main__':unittest.main()
