import pytest

from bfxapi.types.labeler import (
    _RecursiveSerializer,
    _Type,
    compose,
    generate_labeler_serializer,
    generate_recursive_serializer,
    partial,
)


class TestCompose:
    def test_single_decorator(self):
        def add_x(cls):
            cls.x = True
            return cls

        @compose(add_x)
        class Foo:
            pass

        assert Foo.x is True

    def test_multiple_decorators_order(self):
        results = []

        def first(cls):
            results.append("first")
            return cls

        def second(cls):
            results.append("second")
            return cls

        @compose(first, second)
        class Foo:
            pass

        # compose applies in reverse (inner-to-outer), so second runs first
        assert results == ["second", "first"]


class TestPartial:
    def test_missing_fields_default_to_none(self):
        @partial
        class MyType(_Type):
            a: int
            b: str
            c: float

        obj = MyType(a=1, b="hello")
        assert obj.a == 1
        assert obj.b == "hello"
        assert obj.c is None

    def test_all_fields_provided(self):
        @partial
        class MyType(_Type):
            a: int
            b: str

        obj = MyType(a=1, b="hello")
        assert obj.a == 1
        assert obj.b == "hello"

    def test_no_fields_all_none(self):
        @partial
        class MyType(_Type):
            a: int
            b: str

        obj = MyType()
        assert obj.a is None
        assert obj.b is None

    def test_unexpected_keyword_raises(self):
        @partial
        class MyType(_Type):
            a: int

        with pytest.raises(TypeError, match="unexpected keyword argument"):
            MyType(a=1, z=99)


class TestSerializerFlatten:
    def test_flat_mode(self):
        from dataclasses import dataclass

        @dataclass
        class FlatType(_Type):
            a: str
            b: float

        s = generate_labeler_serializer(
            name="FlatType",
            klass=FlatType,
            labels=["_PLACEHOLDER", "a", "b"],
            flat=True,
        )
        # flat=True flattens nested lists
        result = s.parse("ignored", "hello", 3.14)
        assert result.a == "hello"
        assert result.b == 3.14

    def test_flat_nested_input(self):
        from dataclasses import dataclass

        @dataclass
        class FlatType(_Type):
            a: str
            b: float
            c: int

        s = generate_labeler_serializer(
            name="FlatType",
            klass=FlatType,
            labels=["a", "b", "c"],
            flat=True,
        )
        # Nested lists should be flattened
        result = s.parse(["hello", [3.14, 42]])
        assert result.a == "hello"
        assert result.b == 3.14
        assert result.c == 42


class TestRecursiveSerializer:
    def test_recursive_parse(self):
        from dataclasses import dataclass

        @dataclass
        class Inner(_Type):
            x: int
            y: int

        @dataclass
        class Outer(_Type):
            name: str
            inner: Inner

        inner_serializer = generate_labeler_serializer(
            name="Inner", klass=Inner, labels=["x", "y"]
        )

        outer_serializer = generate_recursive_serializer(
            name="Outer",
            klass=Outer,
            labels=["name", "inner"],
            serializers={"inner": inner_serializer},
        )

        result = outer_serializer.parse("test", [10, 20])
        assert isinstance(result, Outer)
        assert result.name == "test"
        assert isinstance(result.inner, Inner)
        assert result.inner.x == 10
        assert result.inner.y == 20

    def test_generate_recursive_serializer_returns_correct_type(self):
        from dataclasses import dataclass

        @dataclass
        class Dummy(_Type):
            a: int

        s = generate_recursive_serializer(
            name="Dummy",
            klass=Dummy,
            labels=["a"],
            serializers={},
        )
        assert isinstance(s, _RecursiveSerializer)
