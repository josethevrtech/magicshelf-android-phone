import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('prepare_phone',Path(__file__).resolve().parents[1]/'backend/prepare_runtime.py')
prepare=importlib.util.module_from_spec(spec);spec.loader.exec_module(prepare)

class PreparationTests(unittest.TestCase):
    def test_failed_preparation_keeps_old_runtime_then_retry_succeeds(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source=root/'steam';source.mkdir()
            (source/'lepton').write_text('new supported runtime');(source/'version.txt').write_text('new version')
            cache=root/'cache';old=cache/'lepton';old.mkdir(parents=True);(old/'old').touch()
            data=root/'android-data';data.mkdir();(data/'apps').write_text('keep my apps')
            env={'MAGICSHELF_CACHE_DIR':str(cache),'MAGICSHELF_STEAM_APP_3029110_DIR':str(source),'MAGICSHELF_BACKEND_DATA_DIR':str(data)}
            with patch.dict(os.environ,env),patch.object(prepare,'build',side_effect=RuntimeError('changed runtime')):
                with self.assertRaises(RuntimeError):prepare.prepare()
            self.assertTrue((old/'old').exists());self.assertEqual((data/'apps').read_text(),'keep my apps')
            with patch.dict(os.environ,env),patch.object(prepare,'build',side_effect=lambda src,dst:(dst/'ready').touch()):prepare.prepare()
            self.assertTrue((old/'ready').exists());self.assertFalse((old/'old').exists())
            with patch.dict(os.environ,env),patch.object(prepare,'build') as build:prepare.prepare();build.assert_not_called()
            self.assertEqual((data/'apps').read_text(),'keep my apps')

    def test_interruption_between_directory_swaps_recovers_the_previous_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            cache=Path(temp);previous=cache/'lepton.previous';previous.mkdir();(previous/'old').touch()
            with patch.dict(os.environ,{'MAGICSHELF_CACHE_DIR':temp,'MAGICSHELF_STEAM_APP_3029110_DIR':temp+'/missing'}):
                with self.assertRaises(RuntimeError):prepare.prepare()
            self.assertTrue((cache/'lepton/old').exists())

if __name__=='__main__':unittest.main()
