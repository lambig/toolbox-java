# toolbox-java

Javaの5つの汎用ライブラリを、一つの依存宣言から利用する入口です。関数合成、タプル、条件分岐、左右の選択、文字列置換を用途に合わせて選べます。toolbox自身は公開Javaクラスを持たず、各ライブラリのAPI契約を所有元で管理します。

実行にはJava 11以上、toolboxのbuildにはJDK 17以上が必要です。Android、JPMS module path、Java 8でtoolbox全体を使う構成はこの版の検証対象に含みません。個別artifactは個別の最低Javaに従って直接利用できます。

## 導入

以下は0.4.0の依存宣言です。利用可能な公開版は[Maven Centralの版一覧](https://repo.maven.apache.org/maven2/io/github/lambig/toolbox-java/)と[リリース記録](https://github.com/lambig/toolbox-java/releases)で確認してください。公開前の候補版は[開発・検証手順](DEVELOPING.md)のcandidateモードで試せます。

Maven:

```xml
<dependency>
  <groupId>io.github.lambig</groupId>
  <artifactId>toolbox-java</artifactId>
  <version>0.4.0</version>
</dependency>
```

Gradle（repositoriesにmavenCentral()を設定）:

```groovy
implementation 'io.github.lambig:toolbox-java:0.4.0'
```

## 対象と用途

| ライブラリ | 選定版 | 用途 | 版付きソース・API文書 |
| --- | --- | --- | --- |
| [functional-interface-extension](https://github.com/lambig/functional-interface-extension/blob/51bce97e473edf056a767a362d4d18d46efe5999/README.md) | 1.1.3 | 関数合成・述語・命題 | [sources](https://repo.maven.apache.org/maven2/io/github/lambig/functional-interface-extension/1.1.3/functional-interface-extension-1.1.3-sources.jar) / [API](https://repo.maven.apache.org/maven2/io/github/lambig/functional-interface-extension/1.1.3/functional-interface-extension-1.1.3-javadoc.jar) |
| [Tuplite](https://github.com/lambig/Tuplite/blob/9eae0778f88280924996a8d5f7551827ff78c0f2/README.md) | 1.0.1 | 2値・3値の組と変換 | [sources](https://repo.maven.apache.org/maven2/io/github/lambig/Tuplite/1.0.1/Tuplite-1.0.1-sources.jar) / [API](https://repo.maven.apache.org/maven2/io/github/lambig/Tuplite/1.0.1/Tuplite-1.0.1-javadoc.jar) |
| [Patterns](https://github.com/lambig/Patterns/blob/5ba5e220d2b735843e865a1480f9793ff19404f4/README.md) | 1.3.2 | 条件の順序に沿う分類と処理 | [sources](https://repo.maven.apache.org/maven2/io/github/lambig/Patterns/1.3.2/Patterns-1.3.2-sources.jar) / [API](https://repo.maven.apache.org/maven2/io/github/lambig/Patterns/1.3.2/Patterns-1.3.2-javadoc.jar) |
| [Union](https://github.com/lambig/Union/blob/e57c7b3ce10b2bc3ec78931feefba08972a2dba1/README.md) | 0.1.1 | 左右どちらか一つの値と合流 | [sources](https://repo.maven.apache.org/maven2/io/github/lambig/Union/0.1.1/Union-0.1.1-sources.jar) / [API](https://repo.maven.apache.org/maven2/io/github/lambig/Union/0.1.1/Union-0.1.1-javadoc.jar) |
| [TextEscape](https://github.com/lambig/TextEscape/blob/745b211a692a8e4e099a0161f2584a3afe660b9c/README.md) | 0.1.1 | 名前付きトークンの文字列置換 | [sources](https://repo.maven.apache.org/maven2/io/github/lambig/TextEscape/0.1.1/TextEscape-0.1.1-sources.jar) / [API](https://repo.maven.apache.org/maven2/io/github/lambig/TextEscape/0.1.1/TextEscape-0.1.1-javadoc.jar) |

API Javadoc JARを展開し、index.htmlを開いてください。表のライブラリ名から、固定した版の導入ガイドと更新説明にも進めます。FIEとUnionのガイドには候補版表記が残るため、公開版の確認には表の成果物リンクを使ってください。公開版の正確なAPIとソースは上の版付き成果物を参照してください。値のnull可否・例外・短絡評価などの契約をtoolbox側で変更しません。

必要な機能が一つだけなら個別artifactを直接宣言できます。toolboxと選定した同じ版の個別artifactを併用しても、同じ座標のJARは一つだけ解決されます。異なる版を明示した場合の最終選択はMaven／Gradleの依存解決に従い、ここに示した組合せ以外は別途検証してください。BOMのような強制的な版統制は行いません。

## 5ライブラリを組み合わせる例

toolboxだけの宣言で、以下の全importをコンパイルできます。[独立例](example/src/main/java/example/ToolboxExample.java)と同じプログラムです。

```java
package example;

import io.github.lambig.funcifextension.function.Functions;
import io.github.lambig.patterns.Patterns;
import io.github.lambig.textescape.TextEscape;
import io.github.lambig.tuplite._2.Tuple2;
import io.github.lambig.union.UnionOf;
import java.util.function.Function;
import java.util.function.Predicate;

public final class ToolboxExample {
    public static void main(String[] args) {
        Function<String, Integer> quantity = Functions.sequenceOf(String::trim, Integer::parseInt);
        Tuple2<Integer, Integer> order = new Tuple2<>(250, quantity.apply(" 4 "));
        int total = order.map((price, count) -> price * count);
        Tuple2<Predicate<Integer>, Function<Integer, String>> large =
                Patterns.when(n -> n >= 1000, Patterns.then("large"));
        String category = Patterns.of(large).orElse("small").apply(total);
        String result = UnionOf.l(total).<String>r().asJoined(Object::toString, reason -> reason);
        String message = TextEscape.escape("${category}: ${total}")
                .where("category", category).where("total", result).compile();
        if (!"large: 1000".equals(message)) throw new AssertionError(message);
        System.out.println(message);
    }
}
```

出力:

```text
large: 1000
```

Maven／Gradleでの実行方法は[DEVELOPING.md](DEVELOPING.md)を参照してください。例ではFunctionsで入力を変換し、Tuple2で金額を計算、Patternsで分類、Unionで一つの結果へ合流し、TextEscapeで表示を組み立てます。Unionは複数エラーの集約を表すResultの代わりではなく、TextEscapeはHTML・SQL・シェル用の無害化を行いません。

## 0.3.1からの更新

0.3.1のクラス同梱方式から、0.4.0ではPOM／Gradle Module Metadataの推移依存で5ライブラリを解決する方式へ変更します。toolboxのJAR単体を手動コピーする運用ではクラスが不足するため、Maven／Gradleが解決した依存JAR一式を実行時に含めてください。旧版へ戻す場合はtoolboxと個別artifactの指定を見直し、同梱JARと個別JARを混在させないでください。

ライブラリのパッケージ名は維持し、Lombokや検査用ライブラリをruntimeへ含めません。旧0.3.1でコンパイルした上の例を新しい依存構成でも実行して検証します。これは代表例のbinary互換性であり、全入力の動作一致ではありません。TextEscapeの特殊文字・既定値処理など、各libraryで修正した旧動作は変わります。

toolboxのsources JARには構成・導入文書・build定義、Javadoc JARには版付きAPI成果物への案内を格納します。各libraryのJavaソースやAPI本文は各artifactのsources／Javadoc JARを取得してください。

## 設計規則とSkeleton

[ab-architecture-rules](https://github.com/lambig/ab-architecture-rules)はABの設計方針を採用する場合にだけ、利用側がテスト依存として追加する任意の検査です。toolboxの標準依存には含みません。[Harnessの導入手順](https://github.com/lambig/ab-architecture-rules#readme)を参照し、検査対象と規則を設定してください。

Skeletonからtoolboxを使う一連の導入・更新の受け入れは[ABService #248](https://github.com/lambig/ABService/issues/248)で追跡しています。ここでの独立例の成功だけでは、その全体受け入れを完了としません。不具合・質問は[Issues](https://github.com/lambig/toolbox-java/issues)へお願いします。
