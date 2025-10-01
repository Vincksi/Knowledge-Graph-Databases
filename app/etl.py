"""
ETL script to migrate data from PostgreSQL to Neo4j.
"""
from utils import wait_for_postgres, wait_for_neo4j, run_cypher, run_cypher_file

import os
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from neo4j import GraphDatabase
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Iterator
from datetime import datetime

def etl():

    wait_for_postgres()
    wait_for_neo4j()

    # Get path to your Cypher schema file
    queries_path = Path(__file__).with_name("queries.cypher")

    # Database connections
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/shop")
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "neo4jpassword")
    
    print("\n" + "="*60)
    print("Starting ETL Process: PostgreSQL → Neo4j")
    print("="*60 + "\n")
    
    # Connect to databases
    print("Connecting to databases...")
    pg_conn = psycopg2.connect(database_url)
    neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    try:
        # Step 1: Clear existing Neo4j data and set up schema
        print("\n[1/6] Clearing existing Neo4j data...")
        run_cypher(neo4j_driver, "MATCH (n) DETACH DELETE n")
        print("  ✓ Neo4j database cleared")
        
        # Execute schema setup if queries.cypher exists
        if queries_path.exists():
            print("\n[2/6] Setting up Neo4j schema...")
            run_cypher_file(neo4j_driver, queries_path)
        else:
            print("\n[2/6] No queries.cypher file found, skipping schema setup")
        
        # Step 2: Extract and Load Categories
        print("\n[3/6] Migrating Categories...")
        df_categories = pd.read_sql("SELECT * FROM categories", pg_conn)
        print(f"  Found {len(df_categories)} categories")
        
        for _, row in df_categories.iterrows():
            run_cypher(neo4j_driver, """
                CREATE (cat:Category {
                    id: $id,
                    name: $name
                })
            """, {
                'id': row['id'],
                'name': row['name']
            })
        print(f"  ✓ Migrated {len(df_categories)} categories")
        
        # Step 3: Extract and Load Products with Category relationships
        print("\n[4/6] Migrating Products...")
        df_products = pd.read_sql("SELECT * FROM products", pg_conn)
        print(f"  Found {len(df_products)} products")
        
        for _, row in df_products.iterrows():
            run_cypher(neo4j_driver, """
                MATCH (cat:Category {id: $category_id})
                CREATE (p:Product {
                    id: $id,
                    name: $name,
                    price: $price
                })
                CREATE (p)-[:IN_CATEGORY]->(cat)
            """, {
                'id': row['id'],
                'name': row['name'],
                'price': float(row['price']),
                'category_id': row['category_id']
            })
        print(f"  ✓ Migrated {len(df_products)} products")
        
        # Step 4: Extract and Load Customers
        print("\n[5/6] Migrating Customers...")
        df_customers = pd.read_sql("SELECT * FROM customers", pg_conn)
        print(f"  Found {len(df_customers)} customers")
        
        for _, row in df_customers.iterrows():
            run_cypher(neo4j_driver, """
                CREATE (c:Customer {
                    id: $id,
                    name: $name,
                    join_date: date($join_date)
                })
            """, {
                'id': row['id'],
                'name': row['name'],
                'join_date': str(row['join_date'])
            })
        print(f"  ✓ Migrated {len(df_customers)} customers")
        
        # Step 5: Extract and Load Orders with relationships
        print("\n[6/6] Migrating Orders and Order Items...")
        df_orders = pd.read_sql("SELECT * FROM orders", pg_conn)
        print(f"  Found {len(df_orders)} orders")
        
        # Create Order nodes and PLACED relationships
        for _, row in df_orders.iterrows():
            # Convert timestamp to ISO 8601 format for Neo4j
            ts_iso = row['ts'].isoformat() if hasattr(row['ts'], 'isoformat') else str(row['ts'])
            run_cypher(neo4j_driver, """
                MATCH (c:Customer {id: $customer_id})
                CREATE (o:Order {
                    id: $id,
                    timestamp: datetime($ts)
                })
                CREATE (c)-[:PLACED]->(o)
            """, {
                'id': row['id'],
                'customer_id': row['customer_id'],
                'ts': ts_iso
            })
        print(f"  ✓ Created {len(df_orders)} orders")
        
        # Load Order Items and create CONTAINS relationships
        df_order_items = pd.read_sql("SELECT * FROM order_items", pg_conn)
        print(f"  Found {len(df_order_items)} order items")
        
        for _, row in df_order_items.iterrows():
            run_cypher(neo4j_driver, """
                MATCH (o:Order {id: $order_id})
                MATCH (p:Product {id: $product_id})
                CREATE (o)-[:CONTAINS {quantity: $quantity}]->(p)
            """, {
                'order_id': row['order_id'],
                'product_id': row['product_id'],
                'quantity': int(row['quantity'])
            })
        print(f"  ✓ Created {len(df_order_items)} order-product relationships")
        
        # Step 6: Extract and Load Events (customer interactions)
        print("\n[Bonus] Migrating Customer Events...")
        df_events = pd.read_sql("SELECT * FROM events", pg_conn)
        print(f"  Found {len(df_events)} events")
        
        for _, row in df_events.iterrows():
            # Convert timestamp to ISO 8601 format for Neo4j
            ts_iso = row['ts'].isoformat() if hasattr(row['ts'], 'isoformat') else str(row['ts'])
            run_cypher(neo4j_driver, """
                MATCH (c:Customer {id: $customer_id})
                MATCH (p:Product {id: $product_id})
                CREATE (c)-[:INTERACTED {
                    event_type: $event_type,
                    timestamp: datetime($ts)
                }]->(p)
            """, {
                'customer_id': row['customer_id'],
                'product_id': row['product_id'],
                'event_type': row['event_type'],
                'ts': ts_iso
            })
        print(f"  ✓ Created {len(df_events)} interaction relationships")
        
        # Summary
        print("\n" + "="*60)
        print("ETL Process Completed Successfully!")
        print("="*60)
        print(f"\nMigrated:")
        print(f"  • {len(df_categories)} categories")
        print(f"  • {len(df_products)} products")
        print(f"  • {len(df_customers)} customers")
        print(f"  • {len(df_orders)} orders")
        print(f"  • {len(df_order_items)} order items")
        print(f"  • {len(df_events)} customer events")
        print("\nGraph structure created:")
        print("  • Category ← IN_CATEGORY ← Product")
        print("  • Customer → PLACED → Order → CONTAINS → Product")
        print("  • Customer → INTERACTED → Product")
        print()
        
    except Exception as e:
        print(f"\n✗ ETL process failed: {e}")
        raise
    finally:
        # Clean up connections
        pg_conn.close()
        neo4j_driver.close()
        print("Database connections closed.\n")


if __name__ == "__main__":
    etl()
