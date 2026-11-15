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

## 公開と追跡

候補版CIは公開物の同一性を保証しません。公開担当者は次の手順で公開先の実物とソースの版を対応付けます。push・タグ・Release・認証操作は適用される承認の範囲で行います。

1. レビュー済みの公開対象コミットをcleanなcheckoutへ固定し、`library-versions.properties`、README、候補版検証が同じ版を指すことを確認します。署名鍵は環境から受け取り、リポジトリには保存しません。
2. `SIGNING_KEY`と`SIGNING_PASSWORD`を設定し、`sh ./gradlew clean check -PreleaseBundle centralBundle`で署名付きbundleを作成します。公開前に内容・署名・秘密情報の混入がないことを確認します。
3. `python3 .github/scripts/release-evidence.py prepare 0.4.0 build/central/toolbox-java-0.4.0-central.zip`で公開元SHAと10成果物の期待ハッシュを保存します。生成先は`build/release-evidence/artifact-checksums.json`です。検証済みbundleをCentralへ登録し、公開完了を確認します。
4. 同じコミットを指す`v0.4.0`タグとGitHub Releaseへ、manifestと公開検証のログを関連付けます。タグが未作成の間もコミットSHAを明示します。公開版に関するソース・文書の案内には、そのタグまたはSHAへの固定リンクを使います。
5. `python3 .github/scripts/release-evidence.py verify 0.4.0 build/release-evidence/artifact-checksums.json`で公開先10ファイルを照合し、`python3 .github/scripts/check-artifacts.py build/public-repository 0.4.0`とpublicモードのconsumerをJava 11／25で実行します。
6. 再実行可能な`Verify public release`ワークフローを版番号付きで実行します。版タグからソースを取得し、同じReleaseのmanifestと公開物を照合して、両Javaのconsumer結果を保存します。Releaseに実行URLを記録し、CI artifactの保存期限内に必要なログをReleaseへ保管します。認証値や非公開情報をログへ含めません。

READMEは版一覧とリリース記録を案内します。同じ「公開済み」表記のためだけに独立した文書PRを必須にせず、必要な文書同期を公開手順へ含めます。文書PRを公開済み成果物の承認ゲートにせず、toolboxを利用する後続の回帰・Skeleton受け入れも独立して進めます。
