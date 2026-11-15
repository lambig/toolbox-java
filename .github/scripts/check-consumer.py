"""Check the resolved runtime, representative binary compatibility, and README example."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.request
from zipfile import ZipFile

classpath_file, version, results_dir = sys.argv[1:]
results = Path(results_dir)
versions = dict(line.split('=', 1) for line in Path('library-versions.properties').read_text().splitlines() if line)
expected = {f'{artifact}-{release}.jar' for artifact, release in versions.items()}
expected.add(f'toolbox-java-{version}.jar')
classpath = Path(classpath_file).read_text().strip()
jars = [Path(p) for p in classpath.split(os.pathsep) if p.endswith('.jar')]
assert len(jars) == len(expected) and {p.name for p in jars} == expected, [p.name for p in jars]
owners = {}
for jar in jars:
    with ZipFile(jar) as z:
        for name in z.namelist():
            if not name.endswith('.class'):
                continue
            assert not name.startswith(('lombok/', 'org/objectweb/asm/')), name
            assert name not in owners, f'duplicate class {name}: {owners.get(name)} / {jar.name}'
            assert int.from_bytes(z.read(name)[6:8], 'big') <= 55, name
            owners[name] = jar.name
assert owners and not any(owner.startswith('toolbox-java-') for owner in owners.values())
readme = Path('README.md').read_text()
source = Path('example/src/main/java/example/ToolboxExample.java').read_text()
assert re.findall(r'```java\n(.*?)```', readme, re.S) == [source]
expected_output = re.findall(r'```text\n(.*?)```', readme, re.S)[0].strip()
for tool in ('gradle', 'maven'):
    assert expected_output in (results / f'{tool}.log').read_text(), tool

# Compile the same example against the old shaded artifact, then execute unchanged
# bytecode with the new resolved runtime. This covers the entry example, not all APIs.
old_jar = Path('build/compatibility/toolbox-java-0.3.1.jar')
old_jar.parent.mkdir(parents=True, exist_ok=True)
if not old_jar.exists():
    urllib.request.urlretrieve('https://repo.maven.apache.org/maven2/io/github/lambig/toolbox-java/0.3.1/toolbox-java-0.3.1.jar', old_jar)
classes = results / 'old-client'
classes.mkdir(exist_ok=True)
subprocess.run([str(Path(os.environ['JAVA_HOME']) / 'bin/javac'), '--release', '11', '-cp', str(old_jar), '-d', str(classes), 'example/src/main/java/example/ToolboxExample.java'], check=True)
java = str(Path(os.environ.get('TEST_JAVA_HOME', os.environ['JAVA_HOME'])) / 'bin/java')
for label, cp in [('old', str(old_jar)), ('new', os.pathsep.join(str(p) for p in jars))]:
    output = subprocess.check_output([java, '-cp', str(classes) + os.pathsep + cp, 'example.ToolboxExample'], text=True).strip()
    assert output == expected_output, (label, output)
(results / 'verification.json').write_text(json.dumps({'jars': sorted(expected), 'classes': len(owners), 'duplicateClasses': 0, 'maximumJava': 11, 'readmeMatches': True, 'oldBinaryExample': True}, indent=2) + '\n')
print('Six resolved JARs; no duplicate classes or extra runtime dependencies; Java 11 bytecode; README and old binary example: OK')
