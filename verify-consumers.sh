#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$root"
mode=${1:-candidate}
version=${2:-0.4.0}
case "$mode" in candidate|public) ;; *) echo 'Usage: verify-consumers.sh [candidate|public] [version]' >&2; exit 2;; esac
case "$version" in ''|*[!0-9.]*|.*|*..*|*.) echo 'Invalid version' >&2; exit 2;; esac
results="$root/build/consumer-results/$mode"
mkdir -p "$results"
repository="$root/build/repository"
if [ "$mode" = candidate ]; then
    library_log=$(mktemp)
    if ! sh ./gradlew --no-daemon --console=plain --warning-mode=all clean publishMavenJavaPublicationToCandidateRepository > "$library_log" 2>&1; then
        mkdir -p "$results"
        mv "$library_log" "$results/library.log"
        exit 1
    fi
    mkdir -p "$results"
    mv "$library_log" "$results/library.log"
    python3 .github/scripts/check-artifacts.py "$repository" "$version" > "$results/artifacts.log" 2>&1
fi
for variant in standalone coexist; do
    result="$results/$variant"
    mkdir -p "$result"
    cache=$(mktemp -d)
    trap 'rm -rf "$cache"' EXIT HUP INT TERM
    if [ "$mode" = candidate ]; then set -- "-PcandidateRepository=$repository"; else set --; fi
    if [ "$variant" = coexist ]; then set -- "$@" -Pcoexist; fi
    GRADLE_USER_HOME="$cache/gradle" sh ./gradlew -p example --no-daemon --console=plain \
        "-PlibraryVersion=$version" "$@" clean runExample writeClasspath > "$result/gradle.log" 2>&1
    if [ "$mode" = candidate ]; then set -- "-DcandidateRepository=file://$repository"; else set --; fi
    if [ "$variant" = coexist ]; then set -- "$@" -Dcoexist; fi
    maven_status=0
    mvn -B -ntp -f example/pom.xml "-Dmaven.repo.local=$cache/maven" "-DlibraryVersion=$version" "$@" \
        -Dorg.slf4j.simpleLogger.log.org.apache.http.client.protocol.ResponseProcessCookies=error \
        -Dorg.slf4j.simpleLogger.log.org.apache.maven.wagon.providers.http.httpclient.client.protocol.ResponseProcessCookies=error \
        clean compile dependency:build-classpath -Dmdep.outputFile=target/runtime-classpath.txt > "$result/maven.log" 2>&1 || maven_status=$?
    # Maven may log a public CDN response cookie. Do not retain it in shared evidence.
    sed -i '/[Ii]nvalid cookie header:/d; /[Ss]et-[Cc]ookie:/d' "$result/maven.log"
    if [ "$maven_status" -ne 0 ]; then exit "$maven_status"; fi
    classpath=$(cat example/target/runtime-classpath.txt)
    "${TEST_JAVA_HOME:-$JAVA_HOME}/bin/java" -cp "example/target/classes:$classpath" example.ToolboxExample >> "$result/maven.log" 2>&1
    for tool in gradle maven; do
        if [ "$tool" = gradle ]; then cpfile=example/build/runtime-classpath.txt; else cpfile=example/target/runtime-classpath.txt; fi
        python3 .github/scripts/check-consumer.py "$cpfile" "$version" "$result" > "$result/$tool-verification.log" 2>&1
    done
    rm -rf "$cache"
    trap - EXIT HUP INT TERM
    echo "Consumer verification passed: $mode $version $variant"
done
