import dataclasses

import datetime
import pytest
from starlette.requests import Request

from ohmyadmin.datasources.datasource import (
    InMemoryDataSource,
    NumberOperation,
    StringOperation,
)

MAX_OBJECTS = 21


@dataclasses.dataclass
class Post:
    id: int = 1
    title: str = "Title"
    author: str = "Title"
    published: bool = False
    date_published: datetime.date | None = dataclasses.field(default_factory=lambda: datetime.datetime.today().date())
    updated_at: datetime.date = dataclasses.field(default_factory=lambda: datetime.datetime.today())


@pytest.fixture
def datasource() -> InMemoryDataSource[Post]:
    return InMemoryDataSource(
        Post,
        [
            Post(
                id=index,
                title=f"Title {index}",
                author=f"Author {index}",
                published=index % 5 == 0,
                date_published=datetime.date(2023, 1, index + 1),
                updated_at=datetime.datetime(2023, 1, index + 1, 12, 0, 0),
            )
            for index in range(MAX_OBJECTS)
        ],
    )


@pytest.fixture()
def http_request() -> Request:
    return Request(scope={"type": "http"})


def test_get_pk(datasource: InMemoryDataSource) -> None:
    obj = Post(id=1)
    assert datasource.get_pk(obj) == "1"


async def test_get(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    obj = await datasource.get(http_request, "2")
    assert obj
    assert obj.id == 2


def test_new(datasource: InMemoryDataSource) -> None:
    assert isinstance(datasource.new(), Post)


def test_query_for_index(datasource: InMemoryDataSource) -> None:
    assert isinstance(datasource.get_query_for_index(), InMemoryDataSource)


async def test_create(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    post = Post(id=100)
    await datasource.create(http_request, post)
    assert await datasource.get(http_request, str(100)) == post


async def test_update(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    obj = await datasource.get(http_request, "1")
    assert obj
    obj.title = "updated"
    await datasource.update(http_request, obj)

    model = await datasource.get(http_request, "1")
    assert model
    assert model.title == "updated"


async def test_delete(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    await datasource.delete(http_request, "1", "2")
    assert not await datasource.get(http_request, "1")
    assert not await datasource.get(http_request, "2")
    assert await datasource.get(http_request, "3")


async def test_search_contains(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    qs = datasource.apply_search_filter("Title 2", searchable_fields=["title"])
    obj = await qs.paginate(http_request, 1, 20)
    assert len(obj.rows) == 2
    assert obj[0].title == "Title 2"
    assert obj[1].title == "Title 20"


async def test_search_starts_with(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    qs = datasource.apply_search_filter("^Title 2", searchable_fields=["title"])
    obj = await qs.paginate(http_request, 1, 20)
    assert len(obj.rows) == 2
    assert obj[0].title == "Title 2"
    assert obj[1].title == "Title 20"


async def test_search_ends_with(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    qs = datasource.apply_search_filter("$2", searchable_fields=["title"])
    obj = await qs.paginate(http_request, 1, 20)
    assert len(obj.rows) == 2
    assert obj[0].title == "Title 2"
    assert obj[1].title == "Title 12"


async def test_search_equals(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    qs = datasource.apply_search_filter("=Title 2", searchable_fields=["title"])
    obj = await qs.paginate(http_request, 1, 20)
    assert len(obj.rows) == 1
    assert obj[0].title == "Title 2"


async def test_search_pattern(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    qs = datasource.apply_search_filter("@Title 1[12]", searchable_fields=["title"])
    obj = await qs.paginate(http_request, 1, 20)
    assert [obj.title for obj in obj.rows] == ["Title 11", "Title 12"]


async def test_sorts_desc(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    qs = datasource.apply_ordering({"title": "desc"}, sortable_fields=["title"])
    obj = await qs.paginate(http_request, 1, 20)
    assert obj[0].title == "Title 9"
    assert obj[1].title == "Title 8"


async def test_sorts_asc(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    qs = datasource.apply_ordering({"title": "asc"}, sortable_fields=["title"])
    obj = await qs.paginate(http_request, 1, 20)
    assert obj[0].title == "Title 0"
    assert obj[1].title == "Title 1"


async def test_sorts_none(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    qs = datasource.apply_ordering({}, sortable_fields=["title"])
    obj = await qs.paginate(http_request, 1, 20)
    assert obj[0].title == "Title 0"
    assert obj[1].title == "Title 1"


async def test_not_sorts_unsupported_fields(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    qs = datasource.apply_ordering({"title": "desc"}, sortable_fields=["id"])
    obj = await qs.paginate(http_request, 1, 20)
    assert obj[0].title == "Title 0"
    assert obj[1].title == "Title 1"


async def test_string_filter_startswith(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    qs = datasource.apply_string_filter("title", StringOperation.STARTSWITH, "Title 2")
    obj = await qs.paginate(http_request, 1, 20)
    assert len(obj.rows) == 2
    assert obj[0].title == "Title 2"
    assert obj[1].title == "Title 20"


async def test_string_filter_endswith(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    qs = datasource.apply_string_filter("title", StringOperation.ENDSWITH, "2")
    obj = await qs.paginate(http_request, 1, 20)
    assert len(obj.rows) == 2
    assert obj[0].title == "Title 2"
    assert obj[1].title == "Title 12"


async def test_string_filter_contains(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    qs = datasource.apply_string_filter("title", StringOperation.CONTAINS, "Title 20")
    obj = await qs.paginate(http_request, 1, 20)
    assert len(obj.rows) == 1
    assert obj[0].title == "Title 20"


async def test_string_filter_pattern(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    qs = datasource.apply_string_filter("title", StringOperation.pattern, r"Title 1([12])")
    obj = await qs.paginate(http_request, 1, 20)
    assert len(obj.rows) == 2
    assert obj[0].title == "Title 11"
    assert obj[1].title == "Title 12"


async def test_string_filter_exact(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    qs = datasource.apply_string_filter("title", StringOperation.EXACT, r"Title 1")
    obj = await qs.paginate(http_request, 1, 20)
    assert len(obj.rows) == 1
    assert obj[0].title == "Title 1"


async def test_number_filter_equals(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    qs = datasource.apply_number_filter("id", NumberOperation.eq, 2)
    obj = await qs.paginate(http_request, 1, 20)
    assert len(obj.rows) == 1
    assert [obj.id for obj in obj] == [2]


async def test_number_filter_gt(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    qs = datasource.apply_number_filter("id", NumberOperation.gt, 19)
    obj = await qs.paginate(http_request, 1, 20)
    assert len(obj.rows) == 1
    assert [obj.id for obj in obj] == [20]


async def test_number_filter_gte(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    qs = datasource.apply_number_filter("id", NumberOperation.gte, 19)
    obj = await qs.paginate(http_request, 1, 20)
    assert len(obj.rows) == 2
    assert [obj.id for obj in obj] == [19, 20]


async def test_number_filter_lt(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    qs = datasource.apply_number_filter("id", NumberOperation.lt, 1)
    obj = await qs.paginate(http_request, 1, 20)
    assert len(obj.rows) == 1
    assert [obj.id for obj in obj] == [0]


async def test_number_filter_lte(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    qs = datasource.apply_number_filter("id", NumberOperation.lte, 1)
    obj = await qs.paginate(http_request, 1, 20)
    assert len(obj.rows) == 2
    assert [obj.id for obj in obj] == [0, 1]


async def test_date_filter(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    qs = datasource.apply_date_filter("date_published", datetime.date(2023, 1, 2))
    obj = await qs.paginate(http_request, 1, 20)
    assert len(obj.rows) == 1
    assert [obj.date_published for obj in obj] == [datetime.date(2023, 1, 2)]


async def test_datetime_filter(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    qs = datasource.apply_date_filter("updated_at", datetime.datetime(2023, 1, 2, 12, 0, 0))
    obj = await qs.paginate(http_request, 1, 20)
    assert len(obj.rows) == 1
    assert [obj.updated_at for obj in obj] == [datetime.datetime(2023, 1, 2, 12, 0, 0)]


async def test_date_range_filter_before(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    qs = datasource.apply_date_range_filter("date_published", before=datetime.date(2023, 1, 2), after=None)
    obj = await qs.paginate(http_request, 1, 20)
    assert [obj.date_published for obj in obj] == [
        datetime.date(2023, 1, 1),
        datetime.date(2023, 1, 2),
    ]


async def test_date_range_filter_null_before(http_request: Request) -> None:
    datasource = InMemoryDataSource(Post, [Post(date_published=None)])
    qs = datasource.apply_date_range_filter("date_published", before=datetime.date(2023, 1, 2), after=None)
    obj = await qs.paginate(http_request, 1, 20)
    assert [obj.date_published for obj in obj] == []


async def test_date_range_filter_null_after(http_request: Request) -> None:
    datasource = InMemoryDataSource(Post, [Post(date_published=None)])
    qs = datasource.apply_date_range_filter("date_published", after=datetime.date(2023, 1, 2), before=None)
    obj = await qs.paginate(http_request, 1, 20)
    assert [obj.date_published for obj in obj] == []


async def test_date_range_filter_after(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    qs = datasource.apply_date_range_filter(
        "date_published", before=None, after=datetime.date(2023, 1, MAX_OBJECTS - 1)
    )
    obj = await qs.paginate(http_request, 1, 20)
    assert [obj.date_published for obj in obj] == [
        datetime.date(2023, 1, 20),
        datetime.date(2023, 1, 21),
    ]


async def test_date_range_filter_between(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    qs = datasource.apply_date_range_filter(
        "date_published",
        after=datetime.date(2023, 1, 2),
        before=datetime.date(2023, 1, 3),
    )
    obj = await qs.paginate(http_request, 1, 20)
    assert [obj.date_published for obj in obj] == [
        datetime.date(2023, 1, 2),
        datetime.date(2023, 1, 3),
    ]


async def test_datetime_range_filter_before(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    qs = datasource.apply_date_range_filter("updated_at", before=datetime.datetime(2023, 1, 2, 12, 0, 0), after=None)
    obj = await qs.paginate(http_request, 1, 20)
    assert [obj.updated_at for obj in obj] == [
        datetime.datetime(2023, 1, 1, 12, 0, 0),
        datetime.datetime(2023, 1, 2, 12, 0, 0),
    ]


async def test_datetime_range_filter_after(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    qs = datasource.apply_date_range_filter(
        "updated_at",
        before=None,
        after=datetime.datetime(2023, 1, MAX_OBJECTS - 1, 12, 0, 0),
    )
    obj = await qs.paginate(http_request, 1, 20)
    assert [obj.updated_at for obj in obj] == [
        datetime.datetime(2023, 1, 20, 12, 0, 0),
        datetime.datetime(2023, 1, 21, 12, 0, 0),
    ]


async def test_datetime_range_filter_between(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    qs = datasource.apply_date_range_filter(
        "updated_at",
        after=datetime.datetime(2023, 1, 2, 12, 0, 0),
        before=datetime.datetime(2023, 1, 3, 12, 0, 0),
    )
    obj = await qs.paginate(http_request, 1, 20)
    assert [obj.updated_at for obj in obj] == [
        datetime.datetime(2023, 1, 2, 12, 0, 0),
        datetime.datetime(2023, 1, 3, 12, 0, 0),
    ]


async def test_choice_filter(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    qs = datasource.apply_choice_filter("title", choices=["Title 1"], coerce=str)
    obj = await qs.paginate(http_request, 1, 20)
    assert [obj.title for obj in obj] == ["Title 1"]


async def test_choice_filter_mismatch(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    qs = datasource.apply_choice_filter("title", choices=["Title 100"], coerce=str)
    obj = await qs.paginate(http_request, 1, 20)
    assert [obj.title for obj in obj] == []


async def test_choice_filter_coerce(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    qs = datasource.apply_choice_filter("id", choices=[1], coerce=int)
    obj = await qs.paginate(http_request, 1, 20)
    assert [obj.id for obj in obj] == [1]


async def test_boolean_filter_true(http_request: Request) -> None:
    datasource = InMemoryDataSource(Post, [Post(id=1, published=True), Post(id=2, published=False)])
    qs = datasource.apply_boolean_filter("published", True)
    obj = await qs.paginate(http_request, 1, 20)
    assert [obj.id for obj in obj] == [1]


async def test_boolean_filter_false(http_request: Request) -> None:
    datasource = InMemoryDataSource(Post, [Post(id=1, published=True), Post(id=2, published=False)])
    qs = datasource.apply_boolean_filter("published", False)
    obj = await qs.paginate(http_request, 1, 20)
    assert [obj.id for obj in obj] == [2]
