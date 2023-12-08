import datetime
import decimal
import pytest
import sqlalchemy as sa
import typing
import uuid
from starlette.requests import Request
from unittest import mock

from ohmyadmin.contrib.sqlalchemy import SQLADataSource
from ohmyadmin.contrib.sqlalchemy.datasource import guess_pk_type
from ohmyadmin.datasources.datasource import NumberOperation, StringOperation
from tests.contrib.sqlalchemy.models import (
    Post,
    PostWithBigIntegerPK,
    PostWithFloatPK,
    PostWithIntegerPK,
    PostWithNumericPK,
    PostWithSmallIntegerPK,
    PostWithStringPK,
    PostWithTextPK,
    PostWithUnsupportedPKType,
    PostWithUUIDPK,
)


@pytest.fixture()
def datasource() -> SQLADataSource[Post]:
    return SQLADataSource(Post)


def test_generates_default_query(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.get_query().raw
    assert "SELECT posts.id, posts.title" in str(sql)


def test_custom_query() -> None:
    sql = SQLADataSource[Post](Post, query=sa.select(Post.id)).get_query().raw
    assert str(sql) == "SELECT posts.id \nFROM posts"


def test_custom_query_for_list() -> None:
    sql = SQLADataSource[Post](Post, query_for_list=sa.select(Post).join(Post.author))
    assert str(sql.get_query_for_index().raw) == (
        "SELECT posts.id, posts.title, posts.date_published, posts.updated_at, "
        "posts.published, posts.author_id \n"
        "FROM posts JOIN users ON users.id = posts.author_id"
    )


def test_detects_pk_column(datasource: SQLADataSource[Post]) -> None:
    assert datasource.pk_column == "id"


def test_detects_pk_column_type(datasource: SQLADataSource[Post]) -> None:
    assert datasource.pk_cast == int


def test_column_type_guesser() -> None:
    assert guess_pk_type(PostWithStringPK, "id") == str
    assert guess_pk_type(PostWithTextPK, "id") == str
    assert guess_pk_type(PostWithIntegerPK, "id") == int
    assert guess_pk_type(PostWithSmallIntegerPK, "id") == int
    assert guess_pk_type(PostWithBigIntegerPK, "id") == int
    assert guess_pk_type(PostWithFloatPK, "id") == float
    assert guess_pk_type(PostWithNumericPK, "id") == decimal.Decimal
    assert guess_pk_type(PostWithUUIDPK, "id") == uuid.UUID

    with pytest.raises(ValueError, match="Failed to guess"):
        guess_pk_type(PostWithUnsupportedPKType, "id")


def test_return_model_pk(datasource: SQLADataSource[Post]) -> None:
    assert datasource.get_pk(Post(id=10)) == "10"


def test_create_new_model(datasource: SQLADataSource[Post]) -> None:
    model = datasource.new()
    assert isinstance(model, Post)
    assert model.id is None


def test_apply_search_contains(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_search_filter("FINDME", ["title"]).raw
    assert "WHERE lower(CAST(posts.title AS TEXT)) LIKE lower(:param_1)" in str(sql)


def test_apply_search_starts_with(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_search_filter("^FINDME", ["title"]).raw
    assert "WHERE (CAST(posts.title AS TEXT) LIKE :param_1 || '%')" in str(sql)


def test_apply_search_ends_with(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_search_filter("$FINDME", ["title"]).raw
    assert "WHERE (CAST(posts.title AS TEXT) LIKE '%' || :param_1)" in str(sql)


def test_apply_search_equals(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_search_filter("=FINDME", ["title"]).raw
    assert "WHERE CAST(posts.title AS TEXT) = :param_1" in str(sql)


def test_apply_search_pattern(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_search_filter("@FINDME1[12]", ["title"]).raw
    assert "WHERE CAST(posts.title AS TEXT) <regexp> :param_1" in str(sql)


def test_apply_search_no_term(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_search_filter("", ["title"]).raw
    assert "WHERE" not in str(sql)


async def test_sorts_desc(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_ordering({"title": "desc"}, sortable_fields=["title"]).raw
    assert "ORDER BY posts.title DESC" in str(sql)


async def test_sorts_asc(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_ordering({"title": "asc"}, sortable_fields=["title"]).raw
    assert "ORDER BY posts.title ASC" in str(sql)


async def test_sorts_relation(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_ordering({"author.name": "asc"}, sortable_fields=["title", "author.name"]).raw
    assert "ORDER BY users.name ASC" in str(sql)


async def test_sorts_none(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_ordering({}, sortable_fields=["title"]).raw
    assert "ORDER BY" not in str(sql)


async def test_not_sorts_unsupported_fields(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_ordering({"title": "desc"}, sortable_fields=["id"]).raw
    assert "ORDER BY" not in str(sql)


async def test_string_filter_startswith(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_string_filter("title", StringOperation.STARTSWITH, "Title 2").raw
    assert "WHERE (lower(posts.title) LIKE :lower_1 || '%')" in str(sql)


async def test_string_filter_endswith(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_string_filter("title", StringOperation.ENDSWITH, "Title 2").raw
    assert "WHERE (lower(posts.title) LIKE '%' || :lower_1)" in str(sql)


async def test_string_filter_contains(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_string_filter("title", StringOperation.CONTAINS, "Title 2").raw
    assert "WHERE lower(posts.title) LIKE :lower_1" in str(sql)


async def test_string_filter_pattern(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_string_filter("title", StringOperation.pattern, "Title 1([12])").raw
    assert "WHERE lower(posts.title) <regexp> :lower_1" in str(sql)


async def test_string_filter_exact(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_string_filter("title", StringOperation.EXACT, "Title 1").raw
    assert "WHERE lower(posts.title) = :lower_1" in str(sql)


async def test_number_filter_equals(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_number_filter("id", NumberOperation.eq, 2).raw
    assert "WHERE CAST(posts.id AS INTEGER) = :param_1" in str(sql)


async def test_number_filter_gt(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_number_filter("id", NumberOperation.gt, 2).raw
    assert "WHERE CAST(posts.id AS INTEGER) > :param_1" in str(sql)


async def test_number_filter_gte(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_number_filter("id", NumberOperation.gte, 2).raw
    assert "WHERE CAST(posts.id AS INTEGER) >= :param_1" in str(sql)


async def test_number_filter_lt(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_number_filter("id", NumberOperation.lt, 2).raw
    assert "WHERE CAST(posts.id AS INTEGER) < :param_1" in str(sql)


async def test_number_filter_lte(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_number_filter("id", NumberOperation.lte, 2).raw
    assert "WHERE CAST(posts.id AS INTEGER) <= :param_1" in str(sql)


async def test_date_filter(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_date_filter("date_published", datetime.date(2023, 1, 2)).raw
    assert "WHERE posts.date_published = :date_published_1" in str(sql)


async def test_datetime_filter(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_date_filter("date_published", datetime.datetime(2023, 1, 2, 12, 0, 0)).raw
    assert "WHERE posts.date_published = :date_published_1" in str(sql)


async def test_date_range_filter_before(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_date_range_filter("date_published", before=datetime.date(2023, 1, 2), after=None).raw
    assert "WHERE posts.date_published <= :date_published_1" in str(sql)


async def test_date_range_filter_after(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_date_range_filter("date_published", before=None, after=datetime.date(2023, 1, 2)).raw
    assert "WHERE posts.date_published >= :date_published_1" in str(sql)


async def test_date_range_filter_between(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_date_range_filter(
        "date_published",
        after=datetime.date(2023, 1, 2),
        before=datetime.date(2023, 1, 3),
    ).raw
    assert "WHERE posts.date_published <= :date_published_1 AND posts.date_published >= :date_published_2" in str(sql)


async def test_datetime_range_filter_before(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_date_range_filter(
        "updated_at", before=datetime.datetime(2023, 1, 2, 12, 0, 0), after=None
    ).raw
    assert "WHERE posts.updated_at <= :updated_at_1" in str(sql)


async def test_datetime_range_filter_after(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_date_range_filter(
        "updated_at", before=None, after=datetime.datetime(2023, 1, 2, 12, 0, 0)
    ).raw
    assert "WHERE posts.updated_at >= :updated_at_1" in str(sql)


async def test_datetime_range_filter_between(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_date_range_filter(
        "updated_at",
        after=datetime.datetime(2023, 1, 2, 12, 0, 0),
        before=datetime.datetime(2023, 1, 3, 12, 0, 0),
    ).raw
    assert "WHERE posts.updated_at <= :updated_at_1 AND posts.updated_at >= :updated_at_2" in str(sql)


async def test_choice_filter(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_choice_filter("title", choices=["Title 1"], coerce=str).raw
    assert "WHERE posts.title IN (__[POSTCOMPILE_title_1])" in str(sql)


async def test_choice_filter_coerce(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_choice_filter("id", choices=[1], coerce=int).raw
    assert "WHERE posts.id IN (__[POSTCOMPILE_id_1])" in str(sql)


async def test_boolean_filter_true(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_boolean_filter("published", True).raw
    assert "WHERE posts.published IS true" in str(sql)


async def test_boolean_filter_false(datasource: SQLADataSource[Post]) -> None:
    sql = datasource.apply_boolean_filter("published", False).raw
    assert "WHERE posts.published IS false" in str(sql)


async def test_count(datasource: SQLADataSource[Post], http_request: Request) -> None:
    result = mock.MagicMock()
    result.one = mock.MagicMock(return_value=100)
    dbsession = mock.AsyncMock()
    dbsession.scalars = mock.AsyncMock(return_value=result)

    http_request.state.dbsession = dbsession
    assert await datasource.count(http_request) == 100
    assert str(dbsession.scalars.call_args[0][0]) == (
        "SELECT count(:count_2) AS count_1 \n"
        "FROM (SELECT posts.id AS id, posts.title AS title, posts.date_published AS "
        "date_published, posts.updated_at AS updated_at, posts.published AS "
        "published, posts.author_id AS author_id \n"
        "FROM posts) AS anon_1"
    )


async def test_get(datasource: SQLADataSource[Post], http_request: Request) -> None:
    model = Post()
    result = mock.MagicMock()
    result.one = mock.MagicMock(return_value=model)
    dbsession = mock.AsyncMock()
    dbsession.scalars = mock.AsyncMock(return_value=result)

    http_request.state.dbsession = dbsession
    assert await datasource.get(http_request, "1") == model
    assert str(dbsession.scalars.call_args[0][0]) == (
        "SELECT posts.id, posts.title, posts.date_published, posts.updated_at, "
        "posts.published, posts.author_id \n"
        "FROM posts \n"
        "WHERE posts.id = :id_1"
    )


async def test_paginate(datasource: SQLADataSource[Post], http_request: Request) -> None:
    model = Post()
    result = mock.MagicMock()
    result.all = mock.MagicMock(return_value=[model])
    dbsession = mock.AsyncMock()
    dbsession.scalars = mock.AsyncMock(return_value=result)

    http_request.state.dbsession = dbsession
    assert (await datasource.paginate(http_request, page=2, page_size=10)).rows == [model]
    assert dbsession.scalars.call_count == 2
    assert str(dbsession.scalars.call_args_list[1].args[0]) == (
        "SELECT posts.id, posts.title, posts.date_published, posts.updated_at, "
        "posts.published, posts.author_id \n"
        "FROM posts\n"
        " LIMIT :param_1 OFFSET :param_2"
    )


async def test_create(datasource: SQLADataSource[Post], http_request: Request) -> None:
    model = Post()
    dbsession = mock.AsyncMock()
    dbsession.add = mock.MagicMock()
    dbsession.commit = mock.AsyncMock()
    http_request.state.dbsession = dbsession

    await datasource.create(http_request, model)

    dbsession.add.assert_called_once_with(model)
    dbsession.commit.assert_called_once_with()


async def test_update(datasource: SQLADataSource[Post], http_request: Request) -> None:
    model = Post()
    dbsession = mock.AsyncMock()
    dbsession.commit = mock.AsyncMock()
    http_request.state.dbsession = dbsession

    await datasource.update(http_request, model)
    dbsession.commit.assert_called_once_with()


async def test_delete(datasource: SQLADataSource[Post], http_request: Request) -> None:
    async def model_generator(self: typing.Any) -> typing.AsyncGenerator[Post, None]:
        yield model
        yield model2

    model = Post()
    model2 = Post()
    dbsession = mock.AsyncMock()
    dbsession.delete = mock.AsyncMock()
    dbsession.commit = mock.AsyncMock()
    dbsession.stream = mock.AsyncMock(side_effect=model_generator)
    http_request.state.dbsession = dbsession

    await datasource.delete(http_request, "1", "2")
    assert dbsession.delete.call_count == 2
    assert dbsession.delete.call_args_list[0][0] == (model,)
    assert dbsession.delete.call_args_list[1][0] == (model2,)
    dbsession.commit.assert_called_once_with()
