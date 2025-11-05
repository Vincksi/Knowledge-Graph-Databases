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
├── app/                               # Application code
│   ├── dockerfile                     # Docker configuration for the FastAPI app
│   ├── etl.py                         # ETL scripts for data transformation
│   ├── main.py                        # FastAPI application
│   ├── queries.cypher                 # Cypher queries for Neo4j
│   ├── requirements.txt               # Python dependencies
│   ├── start.sh                       # Startup script
│   └── utils.py                       # Utility functions
│
├── scripts/                           # Utility scripts
│   ├── check_containers.sh            # Local container health checks
│   └── check_containers_in_docker.sh  # Containerized health checks
│
├── postgres/                          # PostgreSQL configuration
│   └── init/                          # Database initialization scripts
│       ├── db_model.sql               # Database schema
│       └── db_seed.sql                # Sample data
│
├── neo4j/                             # Neo4j data and configuration
│   ├── data/                          # Neo4j database files
│   ├── logs/                          # Log files
│   ├── import/                        # Data import directory
│   └── conf/                          # Configuration files
│
├── dockerfile.checks                  # Dockerfile for health check service
├── docker-compose.yml                 # Docker Compose configuration
├── README.md                          # This file
└── API_USAGE.md                       # API documentation
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

3. **Run health checks**
   To verify that all services are running correctly:
   ```bash
   docker-compose up checks
   ```
   This will run a series of checks including:
   - FastAPI health endpoint
   - PostgreSQL connectivity
   - ETL process execution

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
- `APP_HOST`: Hostname of the FastAPI application (default: app)
- `APP_PORT`: Port of the FastAPI application (default: 8000)
- `PG_HOST`: Hostname of the PostgreSQL server (default: postgres)
- `PG_USER`: PostgreSQL username (default: postgres)
- `PG_PASSWORD`: PostgreSQL password (default: postgres)
- `PG_DB`: PostgreSQL database name (default: shop)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.