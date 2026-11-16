"""Failure-path tests for release evidence, using deliberately synthetic artifact bytes."""
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

SCRIPT = Path(__file__).with_name('release-evidence.py').resolve()
VERSION = '0.4.0'
HEAD = 'a' * 40
PREFIX = f'io/github/lambig/toolbox-java/{VERSION}/'
NAMES = {f'toolbox-java-{VERSION}{suffix}' for suffix in ('.jar', '-sources.jar', '-javadoc.jar', '.pom', '.module')}
NAMES |= {name + '.asc' for name in list(NAMES)}


class ReleaseEvidenceTest(unittest.TestCase):
    def setUp(self):
        self.previous = Path.cwd()
        self.temporary = tempfile.TemporaryDirectory()
        os.chdir(self.temporary.name)
        self.data = {name: ('synthetic fixture: ' + name).encode() for name in NAMES}
        self.bundle()

    def tearDown(self):
        os.chdir(self.previous)
        self.temporary.cleanup()

    def bundle(self, omit=None, extra=None):
        with ZipFile('bundle.zip', 'w') as z:
            for name, data in self.data.items():
                if name != omit:
                    z.writestr(PREFIX + name, data)
            if extra:
                z.writestr(extra, b'synthetic')

    def invoke(self, mode, filename, dirty=False, head=HEAD, data=None):
        def git(args, **kwargs):
            return head + '\n' if args[1] == 'rev-parse' else ('?? unrelated.txt\n' if dirty else '')

        def download(url, **kwargs):
            self.assertTrue(url.startswith('https://repo.maven.apache.org/maven2/' + PREFIX))
            return io.BytesIO((data or self.data)[url.rsplit('/', 1)[-1]])

        with patch.object(sys, 'argv', [str(SCRIPT), mode, VERSION, filename]), \
                patch('subprocess.check_output', side_effect=git), \
                patch('urllib.request.urlopen', side_effect=download), redirect_stdout(io.StringIO()):
            runpy.run_path(str(SCRIPT), run_name='__main__')

    def prepare(self):
        self.invoke('prepare', 'bundle.zip')
        return 'build/release-evidence/artifact-checksums.json'

    def test_round_trip(self):
        manifest = self.prepare()
        self.invoke('verify', manifest)
        self.assertEqual(len(list((Path('build/public-repository') / PREFIX).iterdir())), 10)

    def test_dirty_source_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, 'clean'):
            self.invoke('prepare', 'bundle.zip', dirty=True)

    def test_gradle_parent_directory_entries_are_accepted(self):
        with ZipFile('bundle.zip', 'a') as z:
            for directory in ['io/', 'io/github/', 'io/github/lambig/',
                              'io/github/lambig/toolbox-java/', PREFIX]:
                z.writestr(directory, b'')
        manifest = self.prepare()
        self.invoke('verify', manifest)
        self.assertEqual(set(json.loads(Path(manifest).read_text())['sha256']), NAMES)

    def test_missing_signature_is_rejected(self):
        self.bundle(omit=f'toolbox-java-{VERSION}.pom.asc')
        with self.assertRaisesRegex(AssertionError, 'Incomplete'):
            self.prepare()

    def test_foreign_coordinates_are_rejected(self):
        self.bundle(extra='unrelated/private.txt')
        with self.assertRaisesRegex(AssertionError, 'coordinates'):
            self.prepare()

    def test_wrong_source_is_rejected(self):
        manifest = self.prepare()
        with self.assertRaisesRegex(AssertionError, 'source commit'):
            self.invoke('verify', manifest, head='b' * 40)

    def test_changed_public_artifact_is_rejected(self):
        manifest = self.prepare()
        data = dict(self.data)
        data[f'toolbox-java-{VERSION}.jar'] = b'different synthetic bytes'
        with self.assertRaises(AssertionError):
            self.invoke('verify', manifest, data=data)

    def test_wrong_version_is_rejected(self):
        manifest = self.prepare()
        value = json.loads(Path(manifest).read_text())
        value['version'] = '0.3.1'
        Path(manifest).write_text(json.dumps(value))
        with self.assertRaisesRegex(AssertionError, 'Version'):
            self.invoke('verify', manifest)

    def test_incomplete_manifest_is_rejected(self):
        manifest = self.prepare()
        value = json.loads(Path(manifest).read_text())
        value['sha256'].pop(next(iter(value['sha256'])))
        Path(manifest).write_text(json.dumps(value))
        with self.assertRaisesRegex(AssertionError, 'artifact set'):
            self.invoke('verify', manifest)


if __name__ == '__main__':
    unittest.main()
