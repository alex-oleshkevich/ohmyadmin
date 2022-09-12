import sqlalchemy as sa
from sqlalchemy.orm import backref, declarative_base, query_expression, relationship

metadata = sa.MetaData()
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = sa.Column(sa.BigInteger, primary_key=True)
    first_name = sa.Column(sa.Text)
    last_name = sa.Column(sa.Text)
    email = sa.Column(sa.Text)
    password = sa.Column(sa.Text)
    photo = sa.Column(sa.Text)
    is_active = sa.Column(sa.Boolean)
    created_at = sa.Column(sa.DateTime)

    @property
    def full_name(self) -> str:
        return f'{self.first_name} {self.last_name}'

    def __str__(self) -> str:
        return self.full_name


class Country(Base):
    __tablename__ = 'countries'
    code = sa.Column(sa.Text, primary_key=True)
    name = sa.Column(sa.Text)


class Currency(Base):
    __tablename__ = 'currencies'
    code = sa.Column(sa.Text, primary_key=True)
    name = sa.Column(sa.Text)


class Customer(Base):
    __tablename__ = 'customers'
    id = sa.Column(sa.BigInteger, primary_key=True)
    name = sa.Column(sa.Text)
    email = sa.Column(sa.Text)
    phone = sa.Column(sa.Text)
    birthday = sa.Column(sa.Date)
    created_at = sa.Column(sa.DateTime(True))
    updated_at = sa.Column(sa.DateTime(True))

    addresses = relationship('Address', cascade='all, delete-orphan')
    payments = relationship('Payment', cascade='all, delete-orphan')
    comments = relationship('Comment', cascade='all, delete-orphan')
    orders = relationship('Order', cascade='all, delete-orphan')

    def __str__(self) -> str:
        return self.name


class Address(Base):
    __tablename__ = 'addresses'
    id = sa.Column(sa.BigInteger, primary_key=True)
    street = sa.Column(sa.Text)
    zip = sa.Column(sa.Text)
    city = sa.Column(sa.Text)
    country = sa.Column(sa.ForeignKey('countries.code'))
    customer_id = sa.Column(sa.ForeignKey('customers.id'))


class Payment(Base):
    __tablename__ = 'payments'
    id = sa.Column(sa.BigInteger, primary_key=True)
    reference = sa.Column(sa.Text)
    amount = sa.Column(sa.Numeric)
    currency = sa.Column(sa.ForeignKey('currencies.code'))
    provider = sa.Column(sa.Text)
    method = sa.Column(sa.Text)
    customer_id = sa.Column(sa.ForeignKey('customers.id'))


class Brand(Base):
    __tablename__ = 'brands'
    id = sa.Column(sa.BigInteger, primary_key=True)
    name = sa.Column(sa.Text)
    slug = sa.Column(sa.Text)
    website = sa.Column(sa.Text)
    description = sa.Column(sa.Text)
    visible_to_customers = sa.Column(sa.Boolean, default=True)
    created_at = sa.Column(sa.DateTime(True))
    updated_at = sa.Column(sa.DateTime(True))


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
    name = sa.Column(sa.Text)
    slug = sa.Column(sa.Text)
    description = sa.Column(sa.Text)
    parent_id = sa.Column(sa.ForeignKey('categories.id'))
    visible_to_customers = sa.Column(sa.Boolean, default=True)
    created_at = sa.Column(sa.DateTime(True))
    updated_at = sa.Column(sa.DateTime(True))


class Product(Base):
    __tablename__ = 'products'
    id = sa.Column(sa.BigInteger, primary_key=True)
    name = sa.Column(sa.Text)
    slug = sa.Column(sa.Text)
    description = sa.Column(sa.Text)
    visible = sa.Column(sa.Boolean, default=True)
    availability = sa.Column(sa.DateTime(True))
    brand_id = sa.Column(sa.ForeignKey('brands.id'))
    price = sa.Column(sa.Numeric)
    compare_at_price = sa.Column(sa.Numeric)
    cost_per_item = sa.Column(sa.Numeric)
    sku = sa.Column(sa.Integer)
    quantity = sa.Column(sa.Integer)
    security_stock = sa.Column(sa.Integer)
    barcode = sa.Column(sa.Text)
    can_be_returned = sa.Column(sa.Boolean)
    can_be_shipped = sa.Column(sa.Boolean)
    created_at = sa.Column(sa.DateTime(True))
    updated_at = sa.Column(sa.DateTime(True))

    brand = relationship(Brand)
    images = relationship('Image', cascade='all, delete-orphan')
    comments = relationship('Comment', cascade='all, delete-orphan')
    categories = relationship('Category', secondary=product_categories, cascade='all')

    def add_file_paths_for_images(self, *paths: str) -> None:
        for path in paths:
            self.images.append(Image(image_path=path, product_id=self.id))


class ProductCategory(Base):
    __table__ = product_categories


class Image(Base):
    __tablename__ = 'images'
    id = sa.Column(sa.BigInteger, primary_key=True)
    image_path = sa.Column(sa.Text)
    product_id = sa.Column(sa.ForeignKey('products.id'))


class Comment(Base):
    __tablename__ = 'comments'
    id = sa.Column(sa.BigInteger, primary_key=True)
    title = sa.Column(sa.Text)
    content = sa.Column(sa.Text)
    public = sa.Column(sa.Boolean)
    product_id = sa.Column(sa.ForeignKey('products.id'))
    customer_id = sa.Column(sa.ForeignKey('customers.id'))
    created_at = sa.Column(sa.DateTime(True))


class Order(Base):
    class Status:
        NEW = 'New'
        PROCESSING = 'Processing'
        SHIPPED = 'Shipped'
        DELIVERED = 'Delivered'
        CANCELLED = 'Cancelled'

    __tablename__ = 'orders'
    id = sa.Column(sa.BigInteger, primary_key=True)
    number = sa.Column(sa.Text)
    customer_id = sa.Column(sa.ForeignKey('customers.id'))
    status = sa.Column(sa.Text)
    address = sa.Column(sa.Text)
    city = sa.Column(sa.Text)
    zip = sa.Column(sa.Text)
    notes = sa.Column(sa.Text)
    currency = sa.Column(sa.ForeignKey('currencies.code'))
    country = sa.Column(sa.ForeignKey('countries.code'))
    created_at = sa.Column(sa.DateTime(True))
    updated_at = sa.Column(sa.DateTime(True))

    total_price = query_expression()
    customer = relationship('Customer', cascade='all')
    items = relationship('OrderItem', cascade='all')

    def __str__(self) -> str:
        return self.number


class OrderItem(Base):
    __tablename__ = 'order_items'
    id = sa.Column(sa.BigInteger, primary_key=True)
    order_id = sa.Column(sa.ForeignKey('orders.id'))
    product_id = sa.Column(sa.ForeignKey('products.id'))
    quantity = sa.Column(sa.Integer)
    unit_price = sa.Column(sa.Numeric)

    order = relationship(Order, back_populates='items')
    product = relationship(Product, backref=backref('items', cascade='all, delete-orphan'))
