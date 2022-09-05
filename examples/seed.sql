create table users
(
    id         bigserial primary key,
    first_name text,
    last_name  text,
    email      text not null,
    password   text not null,
    created_at timestamptz default current_timestamp,
    is_active  boolean     default 't'
);

create table countries
(
    code varchar(2) primary key,
    name text
);

create table currencies
(
    code varchar(3) primary key,
    name text
);

create table customers
(
    id         bigserial primary key,
    name       text,
    email      text,
    phone      text,
    birthday   date,
    created_at timestamptz default current_timestamp,
    updated_at timestamptz null
);

create table addresses
(
    id          bigserial primary key,
    street      text,
    zip         text,
    city        text,
    country     varchar(2) references countries,
    customer_id bigint references customers
);

create table payments
(
    id          bigserial primary key,
    reference   text,
    amount      numeric,
    currency    varchar(3) references currencies,
    provider    text,
    method      text,
    customer_id bigint references customers
);

create table brands
(
    id                   serial primary key,
    name                 text,
    slug                 text,
    website              text,
    visible_to_customers boolean     default 't',
    description          text,
    created_at           timestamptz default current_timestamp,
    updated_at           timestamptz null
);

create table categories
(
    id                   bigserial primary key,
    name                 text,
    slug                 text,
    description          text,
    parent               bigint      null references brands,
    visible_to_customers boolean     default 't',
    created_at           timestamptz default current_timestamp,
    updated_at           timestamptz null
);

create table products
(
    id               bigserial primary key,
    name             text,
    slug             text,
    description      text,
    visible          boolean     default 't',
    availability     timestamptz not null,
    brand_id         serial references brands,
    price            numeric     not null,
    compare_at_price numeric,
    cost_per_item    numeric,
    sku              int check ( sku > 0 ),
    quantity         int check ( sku > 0 ),
    security_stock   int check ( sku > 0 ),
    barcode          text        not null,
    can_be_returned  boolean,
    can_be_shipped   boolean,
    created_at       timestamptz default current_timestamp,
    updated_at       timestamptz null
);

create table product_categories
(
    id          bigserial primary key,
    product_id  bigint references products,
    category_id bigint references categories
);

create table images
(
    id         bigserial primary key,
    image_path text not null,
    product_id bigint references products
);

create table comments
(
    id          bigserial primary key,
    title       text,
    public      boolean     default 't',
    content     text,
    customer_id bigint references customers,
    product_id  bigint references products,
    created_at  timestamptz default current_timestamp
);

create table orders
(
    id          bigserial primary key,
    number      text,
    customer_id bigint references customers,
    status      text,
    currency    varchar(3) references currencies,
    country     varchar(2) references countries,
    address     text,
    city        text,
    zip         text,
    notes       text,
    created_at  timestamptz default current_timestamp,
    updated_at  timestamptz null
);

create table order_items
(
    id         serial primary key,
    product_id bigint references products,
    quantity   int check ( quantity > 0 ),
    unit_price numeric
);
