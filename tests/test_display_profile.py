import json
import tempfile
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from display_profile import display_profile
class DisplayProfileTests(unittest.TestCase):
    def test_phone_default_and_persisted_tablet_mode(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'settings.json'
            self.assertEqual(display_profile(p),(720,1600,320))
            p.write_text(json.dumps({'display_mode':'tablet','unrelated':'keep'}))
            self.assertEqual(display_profile(p),(960,1280,240))
            self.assertEqual(json.loads(p.read_text())['unrelated'],'keep')
    def test_bad_or_unknown_settings_keep_a_working_phone(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'settings.json'
            for value in ['broken','[]','{"display_mode":"Android17"}']:
                p.write_text(value);self.assertEqual(display_profile(p),(720,1600,320))