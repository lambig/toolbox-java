# 開発・検証

toolboxはJavaクラスを追加するライブラリではなく、5ライブラリへの依存情報を提供します。buildはJDK 17以上、利用側はJava 11以上です。Gradle Wrapper、Maven 3.8以上、Python 3、POSIXシェルを使用します。

## 候補版

```sh
sh ./verify-consumers.sh candidate 0.4.0
```

`TEST_JAVA_HOME`を指定すると、そのJavaで利用例と旧コンパイル済み例を実行します。CIはbuild JDK 17と実行Java 11／25を組み合わせます。

- POMのcompile依存、Gradleのapi/runtime variant、版と最低Java、Module Metadataのファイルハッシュを検査します。`api`依存とPOMの対応は[Gradleの説明](https://docs.gradle.org/9.7.1/userguide/java_library_plugin.html#sec:java_library_separation)を参照してください。
- toolboxだけを宣言する場合と、選定した5ライブラリを同時に直接宣言する場合を、Maven／Gradleごとの空キャッシュから実行します。
- runtimeがtoolboxと5ライブラリの6 JARであること、重複クラス・Lombok・追加のruntime依存がないこと、全クラスがJava 11以下のbytecodeであることを調べます。
- READMEと独立例のソース・出力を照合します。同じ例を旧0.3.1でコンパイルし、旧版と新構成の両方で実行します。代表例のbinary互換性であり、各APIの全入力を再検査するものではありません。
- 各libraryの公開済みsources／Javadoc JAR計10ファイルを取得し、Javaソース／HTMLが存在し、classを含まないことを検査します。

結果は`build/consumer-results/candidate`にあります。toolbox自身のtestがNO-SOURCEであることを単体試験成功とは数えません。library本体の契約試験は各所有リポジトリで維持します。

## 例を個別に動かす

```sh
sh ./gradlew publishMavenJavaPublicationToCandidateRepository
sh ./gradlew -p example -PcandidateRepository="$PWD/build/repository" runExample
mvn -f example/pom.xml -DcandidateRepository="file://$PWD/build/repository" \
  compile dependency:build-classpath -Dmdep.outputFile=target/runtime-classpath.txt
java -cp "example/target/classes:$(cat example/target/runtime-classpath.txt)" example.ToolboxExample
```

個別artifact併用はGradleに`-Pcoexist`、Mavenに`-Dcoexist`を追加します。公開済みの版は候補リポジトリの引数を外し、Gradleの`-PlibraryVersion=VERSION`／Mavenの`-DlibraryVersion=VERSION`で選択します。公開版の一括consumer確認は次で実行できます。

```sh
sh ./verify-consumers.sh public 0.4.0
```

## 更新・復帰

問題が出た利用側では、最後に成功したコミットの依存宣言・lock・利用コードを一組として戻します。toolboxの版だけを戻して個別artifactの上書きを残すと、元の構成には戻りません。公開済みartifactを上書きせず、次の旧版と実際の解決結果を照合します。個別利用とtoolbox全体の復帰を混在させません。

| 復帰対象 | 旧版の組合せ・依存 | 利用側で確かめる動作 |
| --- | --- | --- |
| FIE単独 | 1.1.2。runtime依存なし | 元配列の変更を反映する命題合成へ戻る。詳細は[所有元の更新説明](https://github.com/lambig/functional-interface-extension/blob/5596a4903266a7117baa22e71596cd1eaac9a446/README.md#更新と切戻し) |
| Tuplite単独 | 1.0.0とFIE 1.0.0（旧POMのcompile依存） | 段階的な構築の可視性が戻るため、[所有元の復帰案内](https://github.com/lambig/Tuplite/blob/9eae0778f88280924996a8d5f7551827ff78c0f2/README.md#型の条件と更新)に沿う |
| Patterns | 1.3.1、Tuplite 1.0.0、FIE 1.1.1。旧POMにはLombok 1.18.28のruntime依存もある | [規則リストの変更を反映する旧動作](https://github.com/lambig/Patterns/blob/5ba5e220d2b735843e865a1480f9793ff19404f4/README.md#131から132への更新)へ戻る。再構築へ移行した利用コードも一緒に戻すかを決め、同じ入力で期待する分類・副作用の順序を試験する |
| Union | 0.1.0。旧POMにはLombok 1.18.24のruntime依存がある | 左右の選択・null・合流の利用側試験を実行する |
| TextEscape | 0.1.0。旧POMにはLombok 1.18.24のruntime依存がある | [修正前の境界動作](https://github.com/lambig/TextEscape/blob/745b211a692a8e4e099a0161f2584a3afe660b9c/README.md#010からの更新)も戻る。ドル記号・バックスラッシュ・キー・既定値について、その利用側が期待する出力と例外を試験する |
| toolbox全体 | 0.3.1の同梱JARのみ。5ライブラリの個別宣言と上書きを外す | 同梱クラスと個別JARの重複を避け、入口例と利用側試験を実行する。同梱内容を現行5版と同一とは扱わない |

個別利用の版の根拠は各旧公開POM（[FIE](https://repo.maven.apache.org/maven2/io/github/lambig/functional-interface-extension/1.1.2/functional-interface-extension-1.1.2.pom)、[Tuplite](https://repo.maven.apache.org/maven2/io/github/lambig/Tuplite/1.0.0/Tuplite-1.0.0.pom)、[Patterns](https://repo.maven.apache.org/maven2/io/github/lambig/Patterns/1.3.1/Patterns-1.3.1.pom)、[Union](https://repo.maven.apache.org/maven2/io/github/lambig/Union/0.1.0/Union-0.1.0.pom)、[TextEscape](https://repo.maven.apache.org/maven2/io/github/lambig/TextEscape/0.1.0/TextEscape-0.1.0.pom)）です。Patternsの旧POMはTuplite/FIEをruntime依存にするため、Tuple2等をコンパイル時に使う利用側は上の版を直接compile/implementation依存として宣言します。複数ライブラリを併用する場合は、各行の旧版を単純に足さず、最後に成功した組合せを復元してください。

復帰後の利用プロジェクトで `mvn dependency:tree`、または `./gradlew dependencies --configuration runtimeClasspath` を実行し、表と異なる版選択・残った上書き・追加runtime依存を確認します。Gradleでは `dependencyInsight --dependency Tuplite --configuration runtimeClasspath` 等で選択理由も追えます。その依存構成でコンパイルし、利用側の回帰試験を実行します。

現行版の確認には既存の `verify-consumers.sh public` を使います。旧版では現行版の依存数・版や修正後動作を固定した検査に合わないため、版引数だけを変えて合格を要求しません。toolbox 0.3.1への復帰は、既存の入口例を次のように実行できます（リポジトリのルート、JDK 17以上）。`coexist` と候補リポジトリを指定しません。

```sh
rollback_cache=$(mktemp -d)
GRADLE_USER_HOME="$rollback_cache/gradle" sh ./gradlew -p example -PlibraryVersion=0.3.1 clean runExample writeClasspath dependencies --configuration runtimeClasspath
mvn -B -ntp -f example/pom.xml "-Dmaven.repo.local=$rollback_cache/maven" -DlibraryVersion=0.3.1 clean compile dependency:tree dependency:build-classpath -Dmdep.outputFile=target/runtime-classpath.txt
java -cp "example/target/classes:$(cat example/target/runtime-classpath.txt)" example.ToolboxExample
```

両方の出力が `large: 1000`、runtimeのJARが `toolbox-java-0.3.1.jar` の1本であることを確認します。これは代表例の成立であり、Patternsの可変規則やTextEscapeの境界動作の一致を保証しません。使っている動作の期待結果を利用側試験で確認して復帰を判断します。

## 公開と追跡

候補版CIは公開物の同一性を保証しません。公開担当者は次の手順で公開先の実物とソースの版を対応付けます。push・タグ・Release・認証操作は適用される承認の範囲で行います。

### 検査が確認する範囲

`prepare`は指定されたbundleの10ファイルのハッシュ、bundle全体の`bundleSha256`、実行時checkoutのHEADを`sourceCommit`へ記録します。cleanであることは検査しますが、bundleがそのHEADから生成されたことは検査しません。同じ版・座標の別コミット由来bundleも受け付けるため、`sourceCommit`は公開担当者が確認する生成元の記録であり、機械的な来歴証明ではありません。

`verify`は公開先10ファイルのバイト列がmanifestの期待ハッシュと一致すること、およびcheckoutのHEADが記録された`sourceCommit`と一致することを確認します。元のbundleを受け取らず、`bundleSha256`を再照合しません。`.asc`もバイト比較の対象であり、署名の暗号学的な検証や署名者の確認は行いません。manifestが正しく作成・保管されていることを前提とする比較で、ソースからの生成、署名の真正性、manifest自体の真正性を証明するものではありません。

生成元の確認は公開担当者の手順に依存します。対象checkoutでのbuildログ・SHA・bundleハッシュを関連付けて保管し、持ち込まれた同版bundleで置き換わっていないことと、期待する署名鍵による署名を公開前に別途確認してください。attestationや再現可能buildとの比較による生成元の機械的証明は、この手順には含みません。

### 実行手順

1. レビュー済みの公開対象コミットをcleanなcheckoutへ固定し、`library-versions.properties`、README、候補版検証が同じ版を指すことを確認します。署名鍵は環境から受け取り、リポジトリには保存しません。
2. `SIGNING_KEY`と`SIGNING_PASSWORD`を設定し、`sh ./gradlew clean check -PreleaseBundle centralBundle`で署名付きbundleを作成します。公開前に内容・署名・秘密情報の混入がないことを確認します。
3. `python3 .github/scripts/release-evidence.py prepare 0.4.0 build/central/toolbox-java-0.4.0-central.zip`でcheckoutのSHAと10成果物の期待ハッシュを保存します。生成先は`build/release-evidence/artifact-checksums.json`です。公開担当者が生成元と署名を確認したbundleをCentralへ登録し、公開完了を確認します。
4. 同じコミットを指す`v0.4.0`タグとGitHub Releaseへ、manifestと公開検証のログを関連付けます。タグが未作成の間もコミットSHAを明示します。公開版に関するソース・文書の案内には、そのタグまたはSHAへの固定リンクを使います。
5. `python3 .github/scripts/release-evidence.py verify 0.4.0 build/release-evidence/artifact-checksums.json`で公開先10ファイルを照合し、`python3 .github/scripts/check-artifacts.py build/public-repository 0.4.0`とpublicモードのconsumerをJava 11／25で実行します。
6. 再実行可能な`Verify public release`ワークフローを版番号付きで実行します。版タグからソースを取得し、同じReleaseのmanifestと公開物を照合して、両Javaのconsumer結果を保存します。Releaseに実行URLを記録し、CI artifactの保存期限内に必要なログをReleaseへ保管します。認証値や非公開情報をログへ含めません。

READMEは版一覧とリリース記録を案内します。同じ「公開済み」表記のためだけに独立した文書PRを必須にせず、必要な文書同期を公開手順へ含めます。文書PRを公開済み成果物の承認ゲートにせず、利用側で独立して進められる回帰・受け入れ作業を止めません。
