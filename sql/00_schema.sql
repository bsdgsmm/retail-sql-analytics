CREATE TABLE categories (
    category_id   INTEGER PRIMARY KEY,
    category_name VARCHAR NOT NULL UNIQUE
);

CREATE TABLE products (
    product_id   INTEGER PRIMARY KEY,
    product_name VARCHAR NOT NULL,
    category_id  INTEGER NOT NULL REFERENCES categories (category_id),
    list_price   DECIMAL(10, 2) NOT NULL CHECK (list_price > 0),
    unit_cost    DECIMAL(10, 2) NOT NULL CHECK (unit_cost > 0),
    launch_date  DATE NOT NULL
);

CREATE TABLE customers (
    customer_id     INTEGER PRIMARY KEY,
    first_name      VARCHAR NOT NULL,
    last_name       VARCHAR NOT NULL,
    email           VARCHAR,
    city            VARCHAR NOT NULL,
    region          VARCHAR NOT NULL,
    signup_date     DATE NOT NULL,
    referral_source VARCHAR
);

CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers (customer_id),
    order_date  DATE NOT NULL,
    channel     VARCHAR NOT NULL CHECK (channel IN ('web', 'mobile_app', 'store')),
    status      VARCHAR NOT NULL CHECK (status IN ('completed', 'cancelled', 'returned')),
    promo_code  VARCHAR
);

CREATE TABLE order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id      INTEGER NOT NULL REFERENCES orders (order_id),
    product_id    INTEGER NOT NULL REFERENCES products (product_id),
    quantity      INTEGER NOT NULL CHECK (quantity > 0),
    unit_price    DECIMAL(10, 2) NOT NULL CHECK (unit_price > 0),
    discount_pct  DECIMAL(4, 2) NOT NULL CHECK (discount_pct >= 0 AND discount_pct < 1)
);
