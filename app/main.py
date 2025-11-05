from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from neo4j import GraphDatabase
import os
from typing import List, Dict, Any
from etl import etl as run_etl

# Database connections
pg_conn = None
neo4j_driver = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database connections
    global pg_conn, neo4j_driver
    
    # PostgreSQL connection
    pg_conn = psycopg2.connect(
        os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/shop")
    )
    
    # Neo4j connection
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "neo4jpassword")
    neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    yield
    
    # Shutdown: Close connections
    if pg_conn:
        pg_conn.close()
    if neo4j_driver:
        neo4j_driver.close()

app = FastAPI(
    title="Shop API",
    description="API for managing shop data with PostgreSQL and Neo4j",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== PostgreSQL Endpoints ====================

@app.get("/")
def read_root():
    """Root endpoint with basic info"""
    return {
        "status": "healthy",
        "message": "Shop API is running",
        "databases": {
            "postgres": "connected" if pg_conn else "disconnected",
            "neo4j": "connected" if neo4j_driver else "disconnected"
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint for container orchestration"""
    if not pg_conn or not neo4j_driver:
        raise HTTPException(status_code=503, detail="Database not connected")
    return {"ok": True}

@app.post("/etl/run")
def trigger_etl(background_tasks: BackgroundTasks):
    """
    Trigger the ETL process to migrate data from PostgreSQL to Neo4j.
    This runs in the background to avoid blocking the API.
    """
    try:
        background_tasks.add_task(run_etl)
        return {
            "status": "started",
            "message": "ETL process started in background. Check logs for progress."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/postgres/customers")
def get_customers():
    """Get all customers from PostgreSQL"""
    try:
        with pg_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM customers ORDER BY join_date DESC")
            customers = cur.fetchall()
        return {"customers": customers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/postgres/customers/{customer_id}")
def get_customer(customer_id: str):
    """Get a specific customer by ID"""
    try:
        with pg_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
            customer = cur.fetchone()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        return customer
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/postgres/products")
def get_products():
    """Get all products with category information"""
    try:
        with pg_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT p.*, c.name as category_name 
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                ORDER BY p.name
            """)
            products = cur.fetchall()
        return {"products": products}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/postgres/orders")
def get_orders():
    """Get all orders with customer information"""
    try:
        with pg_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT o.*, c.name as customer_name
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.id
                ORDER BY o.ts DESC
            """)
            orders = cur.fetchall()
        return {"orders": orders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/postgres/orders/{order_id}")
def get_order_details(order_id: str):
    """Get order details with items"""
    try:
        with pg_conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get order info
            cur.execute("""
                SELECT o.*, c.name as customer_name
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.id
                WHERE o.id = %s
            """, (order_id,))
            order = cur.fetchone()
            
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            
            # Get order items
            cur.execute("""
                SELECT oi.*, p.name as product_name, p.price
                FROM order_items oi
                LEFT JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = %s
            """, (order_id,))
            items = cur.fetchall()
            
            order['items'] = items
            order['total'] = sum(item['quantity'] * float(item['price']) for item in items)
        
        return order
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/postgres/customer/{customer_id}/orders")
def get_customer_orders(customer_id: str):
    """Get all orders for a specific customer"""
    try:
        with pg_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT o.id, o.ts, 
                       COUNT(oi.product_id) as item_count,
                       SUM(oi.quantity * p.price) as total
                FROM orders o
                LEFT JOIN order_items oi ON o.id = oi.order_id
                LEFT JOIN products p ON oi.product_id = p.id
                WHERE o.customer_id = %s
                GROUP BY o.id, o.ts
                ORDER BY o.ts DESC
            """, (customer_id,))
            orders = cur.fetchall()
        return {"customer_id": customer_id, "orders": orders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/postgres/events")
def get_events():
    """Get all customer events"""
    try:
        with pg_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT e.*, c.name as customer_name, p.name as product_name
                FROM events e
                LEFT JOIN customers c ON e.customer_id = c.id
                LEFT JOIN products p ON e.product_id = p.id
                ORDER BY e.ts DESC
            """)
            events = cur.fetchall()
        return {"events": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Neo4j Endpoints ====================

@app.post("/neo4j/migrate")
def migrate_to_neo4j():
    """Migrate data from PostgreSQL to Neo4j"""
    try:
        with neo4j_driver.session() as session:
            # Clear existing data
            session.run("MATCH (n) DETACH DELETE n")
            
            # Migrate customers
            with pg_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM customers")
                customers = cur.fetchall()
                for customer in customers:
                    session.run("""
                        CREATE (c:Customer {
                            id: $id,
                            name: $name,
                            join_date: date($join_date)
                        })
                    """, id=customer['id'], name=customer['name'], 
                         join_date=str(customer['join_date']))
            
            # Migrate categories
            with pg_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM categories")
                categories = cur.fetchall()
                for category in categories:
                    session.run("""
                        CREATE (cat:Category {
                            id: $id,
                            name: $name
                        })
                    """, id=category['id'], name=category['name'])
            
            # Migrate products
            with pg_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM products")
                products = cur.fetchall()
                for product in products:
                    session.run("""
                        MATCH (cat:Category {id: $category_id})
                        CREATE (p:Product {
                            id: $id,
                            name: $name,
                            price: $price
                        })
                        CREATE (p)-[:IN_CATEGORY]->(cat)
                    """, id=product['id'], name=product['name'], 
                         price=float(product['price']), category_id=product['category_id'])
            
            # Migrate orders and relationships
            with pg_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM orders")
                orders = cur.fetchall()
                for order in orders:
                    session.run("""
                        MATCH (c:Customer {id: $customer_id})
                        CREATE (o:Order {
                            id: $id,
                            timestamp: datetime($ts)
                        })
                        CREATE (c)-[:PLACED]->(o)
                    """, id=order['id'], customer_id=order['customer_id'], 
                         ts=str(order['ts']))
            
            # Migrate order items
            with pg_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM order_items")
                items = cur.fetchall()
                for item in items:
                    session.run("""
                        MATCH (o:Order {id: $order_id})
                        MATCH (p:Product {id: $product_id})
                        CREATE (o)-[:CONTAINS {quantity: $quantity}]->(p)
                    """, order_id=item['order_id'], product_id=item['product_id'], 
                         quantity=item['quantity'])
            
            # Migrate events
            with pg_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM events")
                events = cur.fetchall()
                for event in events:
                    session.run("""
                        MATCH (c:Customer {id: $customer_id})
                        MATCH (p:Product {id: $product_id})
                        CREATE (c)-[:INTERACTED {
                            event_type: $event_type,
                            timestamp: datetime($ts)
                        }]->(p)
                    """, customer_id=event['customer_id'], product_id=event['product_id'],
                         event_type=event['event_type'], ts=str(event['ts']))
        
        return {"status": "success", "message": "Data migrated to Neo4j"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/neo4j/customers")
def get_neo4j_customers():
    """Get all customers from Neo4j"""
    try:
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (c:Customer)
                RETURN c.id as id, c.name as name, c.join_date as join_date
                ORDER BY c.name
            """)
            customers = [dict(record) for record in result]
        return {"customers": customers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/neo4j/products")
def get_neo4j_products():
    """Get all products with categories from Neo4j"""
    try:
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (p:Product)-[:IN_CATEGORY]->(cat:Category)
                RETURN p.id as id, p.name as name, p.price as price, 
                       cat.name as category_name
                ORDER BY p.name
            """)
            products = [dict(record) for record in result]
        return {"products": products}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/neo4j/customer/{customer_id}/recommendations")
def get_product_recommendations(customer_id: str):
    """Get product recommendations based on similar customers' purchases"""
    try:
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (c:Customer {id: $customer_id})-[:PLACED]->(:Order)-[:CONTAINS]->(p:Product)
                MATCH (p)<-[:CONTAINS]-(:Order)<-[:PLACED]-(other:Customer)
                WHERE c <> other
                MATCH (other)-[:PLACED]->(:Order)-[:CONTAINS]->(rec:Product)
                WHERE NOT (c)-[:PLACED]->(:Order)-[:CONTAINS]->(rec)
                RETURN rec.id as product_id, rec.name as product_name, 
                       rec.price as price, COUNT(*) as score
                ORDER BY score DESC
                LIMIT 5
            """, customer_id=customer_id)
            recommendations = [dict(record) for record in result]
        return {"customer_id": customer_id, "recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/neo4j/customer/{customer_id}/graph")
def get_customer_graph(customer_id: str):
    """Get customer's purchase graph"""
    try:
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (c:Customer {id: $customer_id})-[:PLACED]->(o:Order)-[r:CONTAINS]->(p:Product)
                RETURN c.name as customer_name, o.id as order_id, 
                       p.name as product_name, r.quantity as quantity
                ORDER BY o.timestamp DESC
            """, customer_id=customer_id)
            graph_data = [dict(record) for record in result]
        return {"customer_id": customer_id, "graph": graph_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/neo4j/product/{product_id}/customers")
def get_product_customers(product_id: str):
    """Get all customers who purchased a specific product"""
    try:
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (c:Customer)-[:PLACED]->(o:Order)-[r:CONTAINS]->(p:Product {id: $product_id})
                RETURN c.id as customer_id, c.name as customer_name, 
                       o.id as order_id, r.quantity as quantity
                ORDER BY o.timestamp DESC
            """, product_id=product_id)
            customers = [dict(record) for record in result]
        return {"product_id": product_id, "customers": customers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/neo4j/analytics/popular-products")
def get_popular_products():
    """Get most popular products by purchase count"""
    try:
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (p:Product)<-[r:CONTAINS]-(:Order)
                RETURN p.id as product_id, p.name as product_name, 
                       SUM(r.quantity) as total_quantity,
                       COUNT(DISTINCT r) as order_count
                ORDER BY total_quantity DESC
                LIMIT 10
            """)
            products = [dict(record) for record in result]
        return {"popular_products": products}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/neo4j/analytics/category-stats")
def get_category_stats():
    """Get statistics by category"""
    try:
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (cat:Category)<-[:IN_CATEGORY]-(p:Product)<-[r:CONTAINS]-(:Order)
                RETURN cat.name as category_name,
                       COUNT(DISTINCT p) as product_count,
                       SUM(r.quantity) as total_sold,
                       SUM(r.quantity * p.price) as total_revenue
                ORDER BY total_revenue DESC
            """)
            stats = [dict(record) for record in result]
        return {"category_stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
