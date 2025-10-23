# Shop API - Usage Guide

## Overview
This FastAPI application provides endpoints to interact with both PostgreSQL and Neo4j databases, along with an ETL process to migrate data between them.

## Starting the Application

```bash
# Start all services
docker compose up -d

# Check logs
docker compose logs -f

# Stop all services
docker compose down
```

## Services

- **PostgreSQL**: `localhost:5432` (user: postgres, password: postgres, db: shop)
- **Neo4j Browser**: `http://localhost:7474` (user: neo4j, password: neo4jpassword)
- **FastAPI**: `http://localhost:8000`
- **API Docs**: `http://localhost:8000/docs`

## API Endpoints

### Health Check
```bash
GET http://localhost:8000/
```

### ETL Process

#### Run ETL Migration
Migrates data from PostgreSQL to Neo4j:
```bash
POST http://localhost:8000/etl/run
```

Or using curl:
```bash
curl -X POST http://localhost:8000/etl/run
```

### PostgreSQL Endpoints

#### Get All Customers
```bash
GET http://localhost:8000/postgres/customers
```

#### Get Customer by ID
```bash
GET http://localhost:8000/postgres/customers/C1
```

#### Get All Products
```bash
GET http://localhost:8000/postgres/products
```

#### Get All Orders
```bash
GET http://localhost:8000/postgres/orders
```

#### Get Order Details
```bash
GET http://localhost:8000/postgres/orders/O1
```

#### Get Customer Orders
```bash
GET http://localhost:8000/postgres/customer/C1/orders
```

#### Get All Events
```bash
GET http://localhost:8000/postgres/events
```

### Neo4j Endpoints

#### Get All Customers (Neo4j)
```bash
GET http://localhost:8000/neo4j/customers
```

#### Get All Products (Neo4j)
```bash
GET http://localhost:8000/neo4j/products
```

#### Get Product Recommendations
Get product recommendations for a customer based on similar customers' purchases:
```bash
GET http://localhost:8000/neo4j/customer/C1/recommendations
```

#### Get Customer Purchase Graph
```bash
GET http://localhost:8000/neo4j/customer/C1/graph
```

#### Get Product Customers
Get all customers who purchased a specific product:
```bash
GET http://localhost:8000/neo4j/product/P1/customers
```

#### Get Popular Products
```bash
GET http://localhost:8000/neo4j/analytics/popular-products
```

#### Get Category Statistics
```bash
GET http://localhost:8000/neo4j/analytics/category-stats
```

## ETL Process Details

The ETL script (`etl.py`) performs the following:

1. **Waits for databases** to be ready
2. **Clears existing Neo4j data**
3. **Sets up schema** using `queries.cypher`
4. **Migrates data** in this order:
   - Categories
   - Products (with IN_CATEGORY relationships)
   - Customers
   - Orders (with PLACED relationships)
   - Order Items (with CONTAINS relationships)
   - Events (with INTERACTED relationships)

### Running ETL Standalone

You can also run the ETL script directly:

```bash
# Inside the container
docker exec -it fastapi-app python etl.py

# Or from your host (if you have the environment set up)
cd app
python etl.py
```

## Neo4j Cypher Queries

After running the ETL, you can explore the graph in Neo4j Browser:

### View all nodes
```cypher
MATCH (n) RETURN n LIMIT 25
```

### Get customer purchase patterns
```cypher
MATCH (c:Customer)-[:PLACED]->(o:Order)-[:CONTAINS]->(p:Product)
RETURN c.name, p.name, o.timestamp
ORDER BY o.timestamp DESC
```

### Find product recommendations
```cypher
MATCH (c:Customer {id: 'C1'})-[:PLACED]->(:Order)-[:CONTAINS]->(p:Product)
MATCH (p)<-[:CONTAINS]-(:Order)<-[:PLACED]-(other:Customer)
WHERE c <> other
MATCH (other)-[:PLACED]->(:Order)-[:CONTAINS]->(rec:Product)
WHERE NOT (c)-[:PLACED]->(:Order)-[:CONTAINS]->(rec)
RETURN rec.name, COUNT(*) as score
ORDER BY score DESC
```

### Category analysis
```cypher
MATCH (cat:Category)<-[:IN_CATEGORY]-(p:Product)<-[r:CONTAINS]-(:Order)
RETURN cat.name, 
       COUNT(DISTINCT p) as products,
       SUM(r.quantity) as total_sold,
       SUM(r.quantity * p.price) as revenue
ORDER BY revenue DESC
```

## Development

### Hot Reload
The FastAPI app runs with `--reload` flag, so changes to Python files will automatically restart the server.

### Adding New Endpoints
Edit `app/main.py` and add your endpoints. The changes will be reflected immediately.

### Modifying ETL Logic
Edit `app/etl.py` to customize the data migration process.

### Schema Changes
Edit `app/queries.cypher` to modify Neo4j constraints and indexes.

## Troubleshooting

### Neo4j not starting
- Check if the `neo4j/data` and `neo4j/import` directories exist
- Check logs: `docker compose logs neo4j`
- Verify password in `docker-compose.yml` matches the one in environment variables

### PostgreSQL connection issues
- Ensure the `postgres/init` directory contains your SQL files
- Check logs: `docker compose logs postgres`

### API not responding
- Check if all services are healthy: `docker compose ps`
- View API logs: `docker compose logs app`
- Rebuild if needed: `docker compose up --build -d`

## Project Structure

```
.
├── docker-compose.yml
├── app/
│   ├── dockerfile
│   ├── requirements.txt
│   ├── main.py            # FastAPI application
│   ├── etl.py             # ETL script
│   └── queries.cypher     # Neo4j schema
├── postgres/
│   └── init/              
│       ├── db_model.sql   # Database schema
│       └── db_seed.sql    # Sample data
└── neo4j/
    ├── data/              # Neo4j data (created by Docker)
    └── import/            # Files for import
```
