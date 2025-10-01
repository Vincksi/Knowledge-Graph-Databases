# Knowledge Graph Databases Project

A comprehensive project demonstrating the integration of PostgreSQL and Neo4j graph database, featuring ETL processes and a FastAPI backend.

## Features

- **PostgreSQL** for structured data storage
- **Neo4j** for graph-based data relationships
- **FastAPI** backend with RESTful endpoints
- **Docker** containerization for easy setup
- **ETL** pipeline for data transformation
- **APOC** and **Graph Data Science** plugins for advanced graph operations

## Project Structure

```
.
├── app/                  # Application code
│   ├── dockerfile        # Docker configuration for the FastAPI app
│   ├── etl.py            # ETL scripts for data transformation
│   ├── main.py           # FastAPI application
│   ├── queries.cypher    # Cypher queries for Neo4j
│   ├── requirements.txt  # Python dependencies
│   ├── start.sh          # Startup script
│   └── utils.py          # Utility functions
├── postgres/
│   ├── init/            # Database initialization scripts
│   ├── db_model.sql     # Database schema
│   └── db_seed.sql      # Sample data
├── neo4j/               # Neo4j data and configuration
├── docker-compose.yml   # Docker Compose configuration
└── README.md            # This file
```

## Prerequisites

- Docker
- Docker Compose
- Python 3.8+

## Getting Started

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Knowledge-Graph-Databases
   ```

2. **Start the services**
   ```bash
   docker-compose up -d
   ```
   This will start:
   - PostgreSQL on port 5432
   - Neo4j Browser on port 7474
   - FastAPI application on port 8000

3. **Access the services**
   - **FastAPI Docs**: http://localhost:8000/docs
   - **Neo4j Browser**: http://localhost:7474
     - Username: neo4j
     - Password: neo4jpassword

## Running ETL Process

The ETL (Extract, Transform, Load) process can be run using the following command:

```bash
docker-compose exec app python etl.py
```

## API Documentation

Once the services are running, you can access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

The application uses the following environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `NEO4J_URI`: Neo4j connection URI
- `NEO4J_USER`: Neo4j username
- `NEO4J_PASSWORD`: Neo4j password

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.