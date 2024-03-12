from __future__ import annotations

import datetime
import decimal

import sqlalchemy as sa
from sqlalchemy.orm import backref, DeclarativeBase, Mapped, mapped_column, query_expression, relationship
from starlette.authentication import BaseUser

metadata = sa.MetaData()


class Base(DeclarativeBase):
    metadata = metadata


class User(BaseUser, Base):
    __tablename__ = "users"
    is_authenticated = True

    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True)
    first_name: Mapped[str] = mapped_column(sa.Text)
    last_name: Mapped[str] = mapped_column(sa.Text)
    email: Mapped[str] = mapped_column(sa.Text, nullable=False)
    password: Mapped[str] = mapped_column(sa.Text)
    photo: Mapped[str] = mapped_column(sa.Text)
    birthdate: Mapped[datetime.date] = mapped_column(sa.Date)
    gender: Mapped[str] = mapped_column()
    balance: Mapped[decimal.Decimal] = mapped_column(default=0)
    rating: Mapped[float] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(sa.DateTime, default=datetime.datetime.now)

    @property
    def identity(self) -> str:
        return str(self.id)

    @property
    def avatar(self) -> str:
        return self.photo or ""

    @property
    def display_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def get_pk(self) -> int:
        return self.id

    def __str__(self) -> str:
        return self.display_name

    def add_file_paths_for_photo(self, path: str) -> None:
        self.photo = path


class Country(Base):
    __tablename__ = "countries"
    code: Mapped[str] = mapped_column(sa.Text, primary_key=True)
    name: Mapped[str] = mapped_column(sa.Text)

    def get_pk(self) -> str:
        return self.code

    def __str__(self) -> str:
        return self.name or "n/a"


class Currency(Base):
    __tablename__ = "currencies"
    code: Mapped[str] = mapped_column(sa.Text, primary_key=True)
    name: Mapped[str] = mapped_column(sa.Text)

    def __str__(self) -> str:
        return self.name or "n/a"


class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(sa.Text)
    email: Mapped[str] = mapped_column(sa.Text)
    phone: Mapped[str] = mapped_column(sa.Text)
    birthday: Mapped[datetime.date] = mapped_column(sa.Date)
    created_at: Mapped[datetime.datetime] = mapped_column(sa.DateTime, default=datetime.datetime.now)
    updated_at: Mapped[datetime.datetime] = mapped_column(sa.DateTime, default=datetime.datetime.now)

    addresses: Mapped[list[Address]] = relationship("Address", cascade="all, delete-orphan")
    payments: Mapped[list[Payment]] = relationship("Payment", cascade="all, delete-orphan")
    comments: Mapped[list[Comment]] = relationship("Comment", cascade="all, delete-orphan")
    orders: Mapped[list[Order]] = relationship("Order", cascade="all, delete-orphan", back_populates="customer")

    def __str__(self) -> str:
        return self.name or "n/a"


class Address(Base):
    __tablename__ = "addresses"
    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True)
    street: Mapped[str] = mapped_column(sa.Text)
    zip: Mapped[str] = mapped_column(sa.Text)
    city: Mapped[str] = mapped_column(sa.Text)
    country: Mapped[str] = mapped_column(sa.ForeignKey("countries.code"))
    customer_id: Mapped[int] = mapped_column(sa.ForeignKey("customers.id"))

    def __str__(self) -> str:
        return self.street or "n/a"


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True)
    reference: Mapped[str] = mapped_column(sa.Text, nullable=False)
    amount: Mapped[str] = mapped_column(sa.Numeric, nullable=False)
    currency_code: Mapped[str] = mapped_column(sa.ForeignKey("currencies.code"), nullable=False)
    provider: Mapped[str] = mapped_column(sa.Text, nullable=False)
    method: Mapped[str] = mapped_column(sa.Text, nullable=False)
    customer_id: Mapped[int] = mapped_column(sa.ForeignKey("customers.id"))

    def __str__(self) -> str:
        return self.reference or "n/a"


class Brand(Base):
    __tablename__ = "brands"
    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    slug: Mapped[str] = mapped_column(sa.Text, nullable=False)
    website: Mapped[str] = mapped_column(sa.Text)
    description: Mapped[str] = mapped_column(sa.Text)
    visible_to_customers: Mapped[bool] = mapped_column(sa.Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(sa.DateTime, default=datetime.datetime.now)
    updated_at: Mapped[datetime.datetime] = mapped_column(sa.DateTime, default=datetime.datetime.now)

    def __str__(self) -> str:
        return self.name or "n/a"


product_categories = sa.Table(
    "product_categories",
    Base.metadata,
    sa.Column("id", sa.BigInteger, primary_key=True),
    sa.Column("product_id", sa.ForeignKey("products.id")),
    sa.Column("category_id", sa.ForeignKey("categories.id")),
)


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    slug: Mapped[str] = mapped_column(sa.Text, nullable=False)
    description: Mapped[str] = mapped_column(sa.Text)
    parent_id: Mapped[int | None] = mapped_column(sa.ForeignKey(id))
    visible_to_customers: Mapped[bool] = mapped_column(sa.Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(sa.DateTime, default=datetime.datetime.now)
    updated_at: Mapped[datetime.datetime] = mapped_column(sa.DateTime, default=datetime.datetime.now)

    parent: Mapped[Category | None] = relationship("Category", back_populates="children", remote_side=[id])
    children: Mapped[list[Category]] = relationship("Category", back_populates="parent")

    def get_pk(self) -> int:
        return self.id

    def __str__(self) -> str:
        return self.name or "n/a"


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    slug: Mapped[str] = mapped_column(sa.Text, nullable=False)
    description: Mapped[str] = mapped_column(sa.Text)
    visible: Mapped[bool] = mapped_column(sa.Boolean, default=True)
    availability: Mapped[datetime.datetime] = mapped_column(sa.DateTime)
    brand_id: Mapped[int] = mapped_column(sa.ForeignKey("brands.id"))
    price: Mapped[float] = mapped_column(sa.Numeric, nullable=False)
    compare_at_price: Mapped[float] = mapped_column(sa.Numeric, nullable=False)
    cost_per_item: Mapped[float] = mapped_column(sa.Numeric, nullable=False)
    sku: Mapped[int] = mapped_column(sa.Integer)
    quantity: Mapped[int] = mapped_column(sa.Integer)
    security_stock: Mapped[int] = mapped_column(sa.Integer)
    barcode: Mapped[str] = mapped_column(sa.Text)
    can_be_returned: Mapped[bool] = mapped_column(sa.Boolean)
    can_be_shipped: Mapped[bool] = mapped_column(sa.Boolean)
    created_at: Mapped[datetime.datetime] = mapped_column(sa.DateTime, default=datetime.datetime.now)
    updated_at: Mapped[datetime.datetime] = mapped_column(sa.DateTime, default=datetime.datetime.now)

    brand: Mapped[Brand] = relationship(Brand)
    images: Mapped[list[Image]] = relationship("Image", cascade="all, delete-orphan")
    comments: Mapped[list[Comment]] = relationship("Comment", cascade="all, delete-orphan")
    categories: Mapped[list[Category]] = relationship("Category", secondary=product_categories)

    def get_pk(self) -> int:
        return self.id

    def __str__(self) -> str:
        return self.name or "n/a"


class ProductCategory(Base):
    __table__ = product_categories
    product_id: Mapped[int]
    category_id: Mapped[int]


class Image(Base):
    __tablename__ = "images"
    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True)
    image_path: Mapped[str] = mapped_column(sa.Text, nullable=False)
    product_id: Mapped[int] = mapped_column(sa.ForeignKey("products.id"))
    product: Mapped[Product] = relationship(Product, back_populates="images")


class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(sa.Text)
    content: Mapped[str] = mapped_column(sa.Text, nullable=False)
    public: Mapped[bool] = mapped_column(sa.Boolean)
    product_id: Mapped[int] = mapped_column(sa.ForeignKey("products.id"))
    customer_id: Mapped[int] = mapped_column(sa.ForeignKey("customers.id"))
    created_at: Mapped[datetime.datetime] = mapped_column(sa.DateTime, default=datetime.datetime.now)

    product: Mapped[Product] = relationship(Product)

    def __str__(self) -> str:
        return self.title or ""


class Order(Base):
    class Status:
        NEW = "New"
        PROCESSING = "Processing"
        SHIPPED = "Shipped"
        DELIVERED = "Delivered"
        CANCELLED = "Cancelled"

        choices = (
            (NEW, NEW),
            (PROCESSING, PROCESSING),
            (SHIPPED, SHIPPED),
            (DELIVERED, DELIVERED),
            (CANCELLED, CANCELLED),
        )

    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True)
    number: Mapped[str] = mapped_column(sa.Text, nullable=False)
    customer_id: Mapped[int] = mapped_column(sa.ForeignKey("customers.id"), nullable=False)
    status: Mapped[str] = mapped_column(sa.Text, nullable=False)
    address: Mapped[str] = mapped_column(sa.Text)
    city: Mapped[str] = mapped_column(sa.Text)
    zip: Mapped[str] = mapped_column(sa.Text)
    notes: Mapped[str] = mapped_column(sa.Text)
    currency_code: Mapped[str] = mapped_column(sa.ForeignKey("currencies.code"), nullable=False)
    country_code: Mapped[str] = mapped_column(sa.ForeignKey("countries.code"), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(sa.DateTime, default=datetime.datetime.now)
    updated_at: Mapped[datetime.datetime] = mapped_column(sa.DateTime, default=datetime.datetime.now)

    total_price: Mapped[float] = query_expression()
    customer: Mapped[Customer] = relationship("Customer", cascade="all", back_populates="orders")
    items: Mapped[list[OrderItem]] = relationship("OrderItem", cascade="all, delete-orphan", back_populates="order")
    currency: Mapped[Currency] = relationship("Currency")
    country: Mapped[Currency] = relationship("Country")

    def __str__(self) -> str:
        return self.number or "n/a"


class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True)
    order_id: Mapped[int] = mapped_column(sa.ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(sa.ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(sa.Integer)
    unit_price: Mapped[float] = mapped_column(sa.Numeric)

    order: Mapped[Order] = relationship(Order, back_populates="items")
    product: Mapped[Product] = relationship(Product, backref=backref("items", cascade="all, delete-orphan"))


class BlogPost(Base):
    __tablename__ = "blog_posts"

    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(
        sa.String,
    )
    content: Mapped[str] = mapped_column(sa.Text, default="")
    author_id: Mapped[int] = mapped_column(sa.ForeignKey(User.id))

    author: Mapped[User] = relationship(User)

    def __str__(self) -> str:
        return self.title
