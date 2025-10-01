// Neo4j Schema Setup
// This file contains Cypher queries to set up constraints and indexes

// Create uniqueness constraints
CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT category_id IF NOT EXISTS FOR (cat:Category) REQUIRE cat.id IS UNIQUE;

CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE;

CREATE CONSTRAINT order_id IF NOT EXISTS FOR (o:Order) REQUIRE o.id IS UNIQUE;

// Create indexes for better query performance
CREATE INDEX customer_name IF NOT EXISTS FOR (c:Customer) ON (c.name);

CREATE INDEX product_name IF NOT EXISTS FOR (p:Product) ON (p.name);

CREATE INDEX product_price IF NOT EXISTS FOR (p:Product) ON (p.price);

CREATE INDEX order_timestamp IF NOT EXISTS FOR (o:Order) ON (o.timestamp);
