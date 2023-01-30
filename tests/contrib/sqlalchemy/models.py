import datetime
import decimal
import sqlalchemy as sa
import typing
import uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    ...


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()


class Post(Base):
    __tablename__ = 'posts'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column()
    date_published: Mapped[datetime.date] = mapped_column()
    updated_at: Mapped[datetime.datetime] = mapped_column()
    published: Mapped[bool] = mapped_column()
    author_id: Mapped[int] = mapped_column(sa.ForeignKey(User.id))
    author: Mapped[User | None] = relationship(User)


class PostWithStringPK(Base):
    __tablename__ = 'posts_with_str_pk'
    id: Mapped[str] = mapped_column(primary_key=True)


class PostWithTextPK(Base):
    __tablename__ = 'posts_with_text_pk'
    id: Mapped[str] = mapped_column(sa.Text, primary_key=True)


class PostWithIntegerPK(Base):
    __tablename__ = 'posts_with_int_pk'
    id: Mapped[int] = mapped_column(primary_key=True)


class PostWithBigIntegerPK(Base):
    __tablename__ = 'posts_with_bigint_pk'
    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True)


class PostWithSmallIntegerPK(Base):
    __tablename__ = 'posts_with_smallint_pk'
    id: Mapped[int] = mapped_column(sa.SmallInteger, primary_key=True)


class PostWithFloatPK(Base):
    __tablename__ = 'posts_with_float_pk'
    id: Mapped[float] = mapped_column(sa.Float, primary_key=True)


class PostWithNumericPK(Base):
    __tablename__ = 'posts_with_numeric_pk'
    id: Mapped[decimal.Decimal] = mapped_column(sa.Numeric, primary_key=True)


class PostWithUUIDPK(Base):
    __tablename__ = 'posts_with_uuid_pk'
    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True)


class PostWithUnsupportedPKType(Base):
    __tablename__ = 'posts_with_unsupported_pk'
    id: Mapped[typing.Any] = mapped_column(sa.Interval, primary_key=True)
