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
