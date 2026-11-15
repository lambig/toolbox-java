"""Record bundle hashes or compare published bytes with the supplied manifest.

The operator must establish the bundle's source and verify its signatures.
sourceCommit records the checkout used by prepare; it is not build provenance.
verify does not consume the bundle, recheck bundleSha256, or authenticate .asc files.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import urllib.request
from zipfile import ZipFile

mode, version, filename = sys.argv[1:]
assert re.fullmatch(r'\d+\.\d+\.\d+', version), 'Expected release version'
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
prefix = f'io/github/lambig/toolbox-java/{version}/'
names = {f'toolbox-java-{version}{suffix}' for suffix in ('.jar', '-sources.jar', '-javadoc.jar', '.pom', '.module')}
names |= {name + '.asc' for name in list(names)}
manifest_path = Path('build/release-evidence/artifact-checksums.json')
manifest_path.parent.mkdir(parents=True, exist_ok=True)
if mode == 'prepare':
    assert not subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip(), 'Release source must be clean'
    bundle = Path(filename)
    with ZipFile(bundle) as z:
        assert all(prefix + n in z.namelist() for n in names), 'Incomplete signed bundle'
        assert all(n.startswith(prefix) for n in z.namelist()), 'Unexpected bundle coordinates'
        digests = {n: hashlib.sha256(z.read(prefix + n)).hexdigest() for n in sorted(names)}
    manifest_path.write_text(json.dumps({'version': version, 'sourceCommit': head, 'bundleSha256': hashlib.sha256(bundle.read_bytes()).hexdigest(), 'sha256': digests}, indent=2) + '\n')
    print(manifest_path)
elif mode == 'verify':
    manifest = json.loads(Path(filename).read_text())
    assert manifest['version'] == version and manifest['sourceCommit'] == head, 'Version/source commit mismatch'
    assert set(manifest['sha256']) == names, 'Unexpected artifact set'
    target = Path('build/public-repository') / prefix
    target.mkdir(parents=True, exist_ok=True)
    for name in sorted(names):
        data = urllib.request.urlopen('https://repo.maven.apache.org/maven2/' + prefix + name, timeout=60).read()
        assert hashlib.sha256(data).hexdigest() == manifest['sha256'][name], name
        (target / name).write_bytes(data)
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Public {version}: ten artifact/signature file hashes match manifest; checkout matches recorded sourceCommit {head}')
    print('Bundle origin, bundleSha256, and signature authenticity are not verified by this command.')
else:
    raise SystemExit('Usage: release-evidence.py prepare|verify VERSION BUNDLE_OR_MANIFEST')
