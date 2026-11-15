"""Validate toolbox metadata and all five libraries' versioned sources/API archives."""
import hashlib
import json
from pathlib import Path
import sys
import urllib.request
import xml.etree.ElementTree as ET
from zipfile import ZipFile

repository, version = sys.argv[1:]
directory = Path(repository) / 'io/github/lambig/toolbox-java' / version
prefix = f'toolbox-java-{version}'
versions = dict(line.split('=', 1) for line in Path('library-versions.properties').read_text().splitlines() if line)
pom = ET.parse(directory / f'{prefix}.pom')
ns = {'m': 'http://maven.apache.org/POM/4.0.0'}
assert pom.findtext('m:version', namespaces=ns) == version
dependencies = pom.findall('m:dependencies/m:dependency', ns)
assert len(dependencies) == 5
actual = {}
for dep in dependencies:
    assert dep.findtext('m:groupId', namespaces=ns) == 'io.github.lambig'
    assert dep.findtext('m:scope', namespaces=ns) == 'compile'
    assert dep.find('m:optional', ns) is None
    actual[dep.findtext('m:artifactId', namespaces=ns)] = dep.findtext('m:version', namespaces=ns)
assert actual == versions, actual
module = json.loads((directory / f'{prefix}.module').read_text())
assert module['component']['version'] == version
for variant in module['variants']:
    if variant['name'] in ('apiElements', 'runtimeElements'):
        assert variant['attributes']['org.gradle.jvm.version'] == 11
        assert len(variant['dependencies']) == 5
        assert {d['module']: d['version']['requires'] for d in variant['dependencies']} == versions
        assert all(d['group'] == 'io.github.lambig' for d in variant['dependencies'])
    for f in variant.get('files', []):
        data = (directory / f['url']).read_bytes()
        assert len(data) == f['size']
        assert hashlib.sha512(data).hexdigest() == f['sha512']
assert {v['name'] for v in module['variants']} >= {'apiElements', 'runtimeElements', 'sourcesElements', 'javadocElements'}
with ZipFile(directory / f'{prefix}.jar') as z:
    assert not any(n.endswith('.class') for n in z.namelist())
    assert z.read('META-INF/library-versions.properties') == Path('library-versions.properties').read_bytes()
with ZipFile(directory / f'{prefix}-sources.jar') as z:
    assert {'README.md', 'DEVELOPING.md', 'build.gradle', 'library-versions.properties'} <= set(z.namelist())
    assert not any(n.endswith('.class') for n in z.namelist())
with ZipFile(directory / f'{prefix}-javadoc.jar') as z:
    html = z.read('index.html').decode('utf-8')
    assert not any(n.endswith('.class') for n in z.namelist())
    for artifact, release in versions.items():
        for classifier in ('sources', 'javadoc'):
            url = f'https://repo.maven.apache.org/maven2/io/github/lambig/{artifact}/{release}/{artifact}-{release}-{classifier}.jar'
            assert url in html, url
            archive = Path('build/dependency-docs') / url.rsplit('/', 1)[-1]
            archive.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(url, archive)
            with ZipFile(archive) as dependency:
                names = dependency.namelist()
                assert not any(n.endswith('.class') for n in names)
                assert any(n.endswith('.java' if classifier == 'sources' else '.html') for n in names)
print('Compile dependencies, Java 11 variants, archive hashes, thin JAR, and ten versioned source/API archives: OK')
