from __future__ import annotations

import datetime
import sqlalchemy as sa
from sqlalchemy.orm import ColumnProperty, backref, declarative_base, query_expression, relationship

from ohmyadmin.auth import UserLike

metadata = sa.MetaData()
Base = declarative_base(metadata=metadata)


class User(Base, UserLike):
    __tablename__ = 'users'

    id = sa.Column(sa.BigInteger, primary_key=True)
    first_name = sa.Column(sa.Text)
    last_name = sa.Column(sa.Text)
    email = sa.Column(sa.Text, nullable=False)
    password = sa.Column(sa.Text)
    photo = sa.Column(sa.Text)
    is_active = sa.Column(sa.Boolean, default=True)
    created_at = sa.Column(sa.DateTime, default=datetime.datetime.now)

    def get_pk(self) -> str:
        return str(self.id)

    def get_id(self) -> str:
        return str(self.id)

    @property
    def avatar(self) -> str:
        return self.photo or ''

    @property
    def full_name(self) -> str:
        return f'{self.first_name} {self.last_name}'

    def __str__(self) -> str:
        return self.full_name

    def add_file_paths_for_photo(self, path: str) -> None:
        self.photo = path


class Country(Base):
    __tablename__ = 'countries'
    code = sa.Column(sa.Text, primary_key=True)
    name = sa.Column(sa.Text)

    def __str__(self) -> str:
        return self.name or 'n/a'


class Currency(Base):
    __tablename__ = 'currencies'
    code = sa.Column(sa.Text, primary_key=True)
    name = sa.Column(sa.Text)

    def __str__(self) -> str:
        return self.name or 'n/a'


class Customer(Base):
    __tablename__ = 'customers'
    id = sa.Column(sa.BigInteger, primary_key=True)
    name = sa.Column(sa.Text)
    email = sa.Column(sa.Text)
    phone = sa.Column(sa.Text)
    birthday = sa.Column(sa.Date)
    created_at = sa.Column(sa.DateTime, default=datetime.datetime.now)
    updated_at = sa.Column(sa.DateTime, default=datetime.datetime.now)

    addresses: list[Address] = relationship('Address', cascade='all, delete-orphan')
    payments: list[Payment] = relationship('Payment', cascade='all, delete-orphan')
    comments: list[Comment] = relationship('Comment', cascade='all, delete-orphan')
    orders: list[Order] = relationship('Order', cascade='all, delete-orphan', back_populates='customer')

    def __str__(self) -> str:
        return self.name or 'n/a'


class Address(Base):
    __tablename__ = 'addresses'
    id = sa.Column(sa.BigInteger, primary_key=True)
    street = sa.Column(sa.Text)
    zip = sa.Column(sa.Text)
    city = sa.Column(sa.Text)
    country: str = sa.Column(sa.ForeignKey('countries.code'))
    customer_id: int = sa.Column(sa.ForeignKey('customers.id'))

    def __str__(self) -> str:
        return self.street or 'n/a'


class Payment(Base):
    __tablename__ = 'payments'
    id = sa.Column(sa.BigInteger, primary_key=True)
    reference = sa.Column(sa.Text, nullable=False)
    amount = sa.Column(sa.Numeric, nullable=False)
    currency_code: str = sa.Column(sa.ForeignKey('currencies.code'), nullable=False)
    provider = sa.Column(sa.Text, nullable=False)
    method = sa.Column(sa.Text, nullable=False)
    customer_id: int = sa.Column(sa.ForeignKey('customers.id'))

    def __str__(self) -> str:
        return self.reference or 'n/a'


class Brand(Base):
    __tablename__ = 'brands'
    id = sa.Column(sa.BigInteger, primary_key=True)
    name = sa.Column(sa.Text, nullable=False)
    slug = sa.Column(sa.Text, nullable=False)
    website = sa.Column(sa.Text)
    description = sa.Column(sa.Text)
    visible_to_customers = sa.Column(sa.Boolean, default=True)
    created_at = sa.Column(sa.DateTime, default=datetime.datetime.now)
    updated_at = sa.Column(sa.DateTime, default=datetime.datetime.now)

    def __str__(self) -> str:
        return self.name or 'n/a'


product_categories = sa.Table(
    'product_categories',
    Base.metadata,
    sa.Column('id', sa.BigInteger, primary_key=True),
    sa.Column('product_id', sa.ForeignKey('products.id')),
    sa.Column('category_id', sa.ForeignKey('categories.id')),
)


class Category(Base):
    __tablename__ = 'categories'
    id = sa.Column(sa.BigInteger, primary_key=True)
    name = sa.Column(sa.Text, nullable=False)
    slug = sa.Column(sa.Text, nullable=False)
    description = sa.Column(sa.Text)
    parent_id: int | None = sa.Column(sa.ForeignKey('categories.id'))
    visible_to_customers = sa.Column(sa.Boolean, default=True)
    created_at = sa.Column(sa.DateTime, default=datetime.datetime.now)
    updated_at = sa.Column(sa.DateTime, default=datetime.datetime.now)

    def __str__(self) -> str:
        return self.name or 'n/a'


class Product(Base):
    __tablename__ = 'products'
    id = sa.Column(sa.BigInteger, primary_key=True)
    name = sa.Column(sa.Text, nullable=False)
    slug = sa.Column(sa.Text, nullable=False)
    description = sa.Column(sa.Text)
    visible = sa.Column(sa.Boolean, default=True)
    availability = sa.Column(sa.DateTime)
    brand_id: int = sa.Column(sa.ForeignKey('brands.id'))
    price = sa.Column(sa.Numeric, nullable=False)
    compare_at_price = sa.Column(sa.Numeric, nullable=False)
    cost_per_item = sa.Column(sa.Numeric, nullable=False)
    sku = sa.Column(sa.Integer)
    quantity = sa.Column(sa.Integer)
    security_stock = sa.Column(sa.Integer)
    barcode = sa.Column(sa.Text)
    can_be_returned = sa.Column(sa.Boolean)
    can_be_shipped = sa.Column(sa.Boolean)
    created_at = sa.Column(sa.DateTime, default=datetime.datetime.now)
    updated_at = sa.Column(sa.DateTime, default=datetime.datetime.now)

    brand: Brand = relationship(Brand)
    images: list[Image] = relationship('Image', cascade='all, delete-orphan')
    comments: list[Comment] = relationship('Comment', cascade='all, delete-orphan')
    categories: list[Category] = relationship('Category', secondary=product_categories)

    def __str__(self) -> str:
        return self.name or 'n/a'


class ProductCategory(Base):
    product_id: int
    category_id: int
    __table__ = product_categories


class Image(Base):
    __tablename__ = 'images'
    id = sa.Column(sa.BigInteger, primary_key=True)
    image_path = sa.Column(sa.Text, nullable=False)
    product_id: int = sa.Column(sa.ForeignKey('products.id'))


class Comment(Base):
    __tablename__ = 'comments'
    id = sa.Column(sa.BigInteger, primary_key=True)
    title = sa.Column(sa.Text)
    content = sa.Column(sa.Text, nullable=False)
    public = sa.Column(sa.Boolean)
    product_id: int = sa.Column(sa.ForeignKey('products.id'))
    customer_id: int = sa.Column(sa.ForeignKey('customers.id'))
    created_at = sa.Column(sa.DateTime, default=datetime.datetime.now)

    def __str__(self) -> str:
        return self.title or ''


class Order(Base):
    class Status:
        NEW = 'New'
        PROCESSING = 'Processing'
        SHIPPED = 'Shipped'
        DELIVERED = 'Delivered'
        CANCELLED = 'Cancelled'

    __tablename__ = 'orders'
    id = sa.Column(sa.BigInteger, primary_key=True)
    number = sa.Column(sa.Text, nullable=False)
    customer_id: int = sa.Column(sa.ForeignKey('customers.id'), nullable=False)
    status = sa.Column(sa.Text, nullable=False)
    address = sa.Column(sa.Text)
    city = sa.Column(sa.Text)
    zip = sa.Column(sa.Text)
    notes = sa.Column(sa.Text)
    currency_code: str = sa.Column(sa.ForeignKey('currencies.code'), nullable=False)
    country_code: str = sa.Column(sa.ForeignKey('countries.code'), nullable=False)
    created_at = sa.Column(sa.DateTime, default=datetime.datetime.now)
    updated_at = sa.Column(sa.DateTime, default=datetime.datetime.now)

    total_price: ColumnProperty = query_expression()
    customer: Customer = relationship('Customer', cascade='all', back_populates='orders')
    items: OrderItem = relationship('OrderItem', cascade='all')
    currency: Currency = relationship('Currency')

    def __str__(self) -> str:
        return self.number or 'n/a'


class OrderItem(Base):
    __tablename__ = 'order_items'
    id = sa.Column(sa.BigInteger, primary_key=True)
    order_id: int = sa.Column(sa.ForeignKey('orders.id'), nullable=False)
    product_id: int = sa.Column(sa.ForeignKey('products.id'), nullable=False)
    quantity = sa.Column(sa.Integer)
    unit_price = sa.Column(sa.Numeric)

    order: Order = relationship(Order, back_populates='items')
    product: Product = relationship(Product, backref=backref('items', cascade='all, delete-orphan'))
