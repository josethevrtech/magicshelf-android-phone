import importlib.util
from pathlib import Path
import unittest
import json
import os
import runpy
import subprocess
import tempfile
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('display_controls', Path(__file__).resolve().parents[1]/'backend/display_controls.py')
controls = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controls)


class TextSizeTests(unittest.TestCase):
    def test_android_scale_is_bounded_and_rounds_slider_steps(self):
        self.assertEqual(controls.font_scale(.2), .85)
        self.assertEqual(controls.font_scale(4), 1.5)
        self.assertEqual(controls.font_scale(1.15000001), 1.15)
        self.assertEqual(controls.font_scale('1.3'), 1.3)

    def test_invalid_values_never_enter_a_shell_command(self):
        for value in ('nan', 'inf', '-inf', '1; reboot', None):
            with self.subTest(value=value), self.assertRaises((ValueError, TypeError)):
                controls.font_scale(value)


class DisplayCompatibilityTests(unittest.TestCase):
    def provision(self, directory, result):
        base=Path(directory)
        for name in ('phone-controls-provisioned.json','phone-brightness-provisioned.json'):
            (base/name).write_text('{}')
        with patch.dict(os.environ, {'MAGICSHELF_DATA_DIR':str(base)}), \
             patch('subprocess.run',return_value=result), \
             patch('subprocess.check_output',return_value='new state: disabled') as command:
            runpy.run_path(str(Path(__file__).resolve().parents[1]/'backend/provision_controls.py'))
        return command

    def test_absent_optional_package_is_expected_not_a_boot_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            result=subprocess.CompletedProcess([],1,stdout='',stderr='')
            command=self.provision(temp,result)
            args=command.call_args.args[0]
            self.assertEqual(args[3:6],['/system/bin/pm','disable','--user'])
            self.assertEqual(args[-1],'com.android.settings/.Settings$DisplaySettingsActivity')
            stamp=Path(temp)/'phone-display-compatibility.json'
            self.assertEqual(json.loads(stamp.read_text())['reason'],'missing-lineageparts')
            self.assertFalse(self.provision(temp,result).called)

    def test_supported_runtime_keeps_android_display_settings(self):
        with tempfile.TemporaryDirectory() as temp:
            result=subprocess.CompletedProcess([],0,stdout='package:/system/LineageParts.apk',stderr='')
            self.assertFalse(self.provision(temp,result).called)
            self.assertFalse((Path(temp)/'phone-display-compatibility.json').exists())

    def test_package_manager_error_does_not_disable_components(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(RuntimeError,'offline'):
                self.provision(temp,subprocess.CompletedProcess([],2,stdout='',stderr='offline'))
