CREATE TABLE customers (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  join_date DATE NOT NULL
);

CREATE TABLE categories (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL
);

CREATE TABLE products (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  price NUMERIC NOT NULL,
  category_id TEXT REFERENCES categories(id)
);

CREATE TABLE orders (
  id TEXT PRIMARY KEY,
  customer_id TEXT REFERENCES customers(id),
  ts TIMESTAMPTZ NOT NULL
);

CREATE TABLE order_items (
  order_id TEXT REFERENCES orders(id),
  product_id TEXT REFERENCES products(id),
  quantity INT NOT NULL,
  PRIMARY KEY (order_id, product_id)
);

-- Optional: behavioral events for CF and embeddings
CREATE TABLE events (
  id TEXT PRIMARY KEY,
  customer_id TEXT REFERENCES customers(id),
  product_id TEXT REFERENCES products(id),
  event_type TEXT CHECK (event_type IN ('view','click','add_to_cart')),
  ts TIMESTAMPTZ NOT NULL
);