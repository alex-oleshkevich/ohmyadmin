#!/usr/bin/env python
import asyncio
import decimal
import random
import sqlalchemy as sa
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from examples.models import (
    Address,
    Brand,
    Category,
    Comment,
    Country,
    Currency,
    Customer,
    Image,
    Order,
    OrderItem,
    Payment,
    Product,
    ProductCategory,
    User,
)

fake = Faker()
TABLES = [
    'users',
    'countries',
    'currencies',
    'customers',
    'addresses',
    'payments',
    'brands',
    'categories',
    'products',
    'product_categories',
    'images',
    'comments',
    'orders',
    'order_items',
]

COUNTRIES = [
    dict(code='us', name='USA'),
    dict(code='by', name='Belarus'),
    dict(code='pl', name='Poland'),
    dict(code='ua', name='Ukraine'),
    dict(code='uk', name='UK'),
    dict(code='lt', name='Lithuania'),
    dict(code='lv', name='Latvia'),
    dict(code='de', name='Germany'),
    dict(code='fr', name='France'),
    dict(code='jp', name='Japan'),
]

CURRENCIES = [
    dict(code='eur', name='Euro'),
    dict(code='usd', name='US Dollar'),
    dict(code='byn', name='Belarusian taler'),
    dict(code='pln', name='Polish zloty'),
]

PAYMENT_PROVIDER = [
    'PayPal',
    'Stripe',
]

PAYMENT_METHOD = [
    'Bank transfer',
    'Credit Card',
    'PayPal',
    'Cash',
]

OBJECTS_COUNT = 1000
STATUSES = ['New', 'Processing', 'Shipped', 'Delivered', 'Cancelled']


def random_status() -> str:
    return STATUSES[random.randint(0, len(STATUSES) - 1)]


def random_country() -> str:
    return COUNTRIES[random.randint(0, len(COUNTRIES) - 1)]['code']


def random_currency() -> str:
    return CURRENCIES[random.randint(0, len(CURRENCIES) - 1)]['code']


def refcode() -> str:
    return ''.join(
        [
            fake.random_letter(),
            fake.random_letter(),
            fake.random_letter(),
            str(random.randint(100_000, 999_999)),
        ]
    ).upper()


def seed_users(session: AsyncSession) -> None:
    session.add_all(
        [
            User(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.email(safe=False),
                password=fake.password(),
                created_at=fake.date_between(),
                is_active=False if index % 10 == 0 else True,
            )
            for index in range(1, OBJECTS_COUNT + 1)
        ]
    )


def seed_countries(session: AsyncSession) -> None:
    session.add_all([Country(code=country['code'], name=country['name']) for country in COUNTRIES])


def seed_currencies(session: AsyncSession) -> None:
    session.add_all([Currency(code=item['code'], name=item['name']) for item in CURRENCIES])


def seed_customers(session: AsyncSession) -> None:
    session.add_all(
        [
            Customer(
                name=fake.name(),
                email=fake.email(safe=False),
                phone=fake.phone_number(),
                birthday=fake.date_of_birth(),
                created_at=fake.date_between(),
                updated_at=fake.date_between(),
            )
            for index in range(1, OBJECTS_COUNT + 1)
        ]
    )


def seed_addresses(session: AsyncSession) -> None:
    session.add_all(
        [
            Address(
                street=fake.street_address(),
                zip=fake.postcode(),
                city=fake.city(),
                country=COUNTRIES[random.randint(0, len(COUNTRIES) - 1)]['code'],
                customer_id=random.randint(1, OBJECTS_COUNT),
            )
            for index in range(1, OBJECTS_COUNT + 1)
        ]
    )


def seed_payment(session: AsyncSession) -> None:
    session.add_all(
        [
            Payment(
                reference=refcode(),
                amount=random.randint(0, 20),
                currency=CURRENCIES[random.randint(0, len(CURRENCIES) - 1)]['code'],
                provider=PAYMENT_PROVIDER[random.randint(0, len(PAYMENT_PROVIDER) - 1)],
                method=PAYMENT_METHOD[random.randint(0, len(PAYMENT_METHOD) - 1)],
                customer_id=random.randint(1, 500),
            )
            for index in range(1, OBJECTS_COUNT + 1)
        ]
    )


def seed_brands(session: AsyncSession) -> None:
    session.add_all(
        [
            Brand(
                name=fake.sentence(3),
                slug=fake.slug(),
                website=fake.url(),
                description=fake.text(),
                visible_to_customers=fake.boolean(),
                created_at=fake.date_between(),
                updated_at=fake.date_between(),
            )
            for index in range(1, 21)
        ]
    )


def seed_categories(session: AsyncSession) -> None:
    session.add_all(
        [
            Category(
                name=fake.sentence(3),
                slug=fake.slug(),
                description=fake.text(),
                parent=random.randint(1, 21) if index % 5 == 0 else None,
                visible_to_customers=fake.boolean(),
                created_at=fake.date_between(),
                updated_at=fake.date_between(),
            )
            for index in range(1, 21)
        ]
    )


def seed_products(session: AsyncSession) -> None:
    session.add_all(
        [
            Product(
                name=fake.sentence(3),
                slug=fake.slug(),
                description=fake.text(),
                visible=fake.boolean(),
                availability=fake.date_between(),
                brand_id=random.randint(1, 20),
                price=decimal.Decimal(f'{random.randint(1, 500)}.{random.randint(1, 99):02}'),
                compare_at_price=decimal.Decimal(f'{random.randint(1, 500)}.{random.randint(1, 99):02}'),
                cost_per_item=decimal.Decimal(f'{random.randint(1, 500)}.{random.randint(1, 99):02}'),
                sku=random.randint(1, 100),
                quantity=random.randint(1, 100),
                security_stock=random.randint(1, 1000),
                barcode=fake.ean(),
                can_be_returned=fake.boolean(),
                can_be_shipped=fake.boolean(),
                created_at=fake.date_between(),
                updated_at=fake.date_between(),
            )
            for index in range(1, OBJECTS_COUNT + 1)
        ]
    )


def seed_product_categories(session: AsyncSession) -> None:
    session.add_all(
        [
            ProductCategory(
                product_id=random.randint(1, OBJECTS_COUNT),
                category_id=random.randint(1, 20),
            )
            for index in range(1, (OBJECTS_COUNT + 1 * 20))
        ]
    )


def seed_product_images(session: AsyncSession) -> None:
    session.add_all(
        [
            Image(
                image_path=fake.image_url(1280, 720),
                product_id=random.randint(1, OBJECTS_COUNT),
            )
            for index in range(1, OBJECTS_COUNT * 3)
        ]
    )


def seed_product_comments(session: AsyncSession) -> None:
    session.add_all(
        [
            Comment(
                title=fake.sentence(6),
                content=fake.text(),
                public=fake.boolean(),
                product_id=random.randint(1, OBJECTS_COUNT),
                customer_id=random.randint(1, OBJECTS_COUNT),
                created_at=fake.date_between(),
            )
            for index in range(1, OBJECTS_COUNT * 5)
        ]
    )


def seed_orders(session: AsyncSession) -> None:
    session.add_all(
        [
            Order(
                number=refcode(),
                customer_id=random.randint(1, OBJECTS_COUNT),
                status=random_status(),
                address=fake.street_address(),
                city=fake.city(),
                zip=fake.postalcode(),
                notes=fake.text(),
                currency=random_currency(),
                country=random_country(),
                created_at=fake.date_between(),
                updated_at=fake.date_between(),
            )
            for index in range(1, OBJECTS_COUNT)
        ]
    )


def seed_order_items(session: AsyncSession) -> None:
    session.add_all(
        [
            OrderItem(
                order_id=random.randint(1, OBJECTS_COUNT - 1),
                product_id=random.randint(1, OBJECTS_COUNT),
                quantity=random.randint(1, 100),
                unit_price=decimal.Decimal(f'{random.randint(1, 500)}.{random.randint(1, 99):02}'),
            )
            for index in range(1, OBJECTS_COUNT * 5)
        ]
    )


async def main():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost/ohmyadmin', future=True)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        for table in TABLES:
            await conn.execute(sa.text(f'truncate {table} restart identity cascade'))

    seeders = [
        seed_users,
        seed_countries,
        seed_currencies,
        seed_customers,
        seed_addresses,
        seed_payment,
        seed_brands,
        seed_categories,
        seed_products,
        seed_product_categories,
        seed_product_images,
        seed_product_comments,
        seed_orders,
        seed_order_items,
    ]

    async with async_session() as session:  # type: AsyncSession
        for seeder in seeders:
            seeder(session)
            await session.flush()

        await session.commit()


asyncio.run(main())
