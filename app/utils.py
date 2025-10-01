
import os
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from neo4j import GraphDatabase
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Iterator


def wait_for_postgres(max_retries: int = 30, delay: int = 2) -> None:
    """
    Waits for PostgreSQL to be ready.
    
    Args:
        max_retries: Maximum number of connection attempts
        delay: Delay in seconds between retries
    
    Raises:
        Exception: If PostgreSQL is not ready after max_retries
    """
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/shop")
    
    print("Waiting for PostgreSQL to be ready...")
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(database_url)
            conn.close()
            print("✓ PostgreSQL is ready!")
            return
        except psycopg2.OperationalError as e:
            if attempt < max_retries - 1:
                print(f"  Attempt {attempt + 1}/{max_retries}: PostgreSQL not ready yet, retrying in {delay}s...")
                time.sleep(delay)
            else:
                raise Exception(f"PostgreSQL not ready after {max_retries} attempts") from e


def wait_for_neo4j(max_retries: int = 30, delay: int = 2) -> None:
    """
    Waits for Neo4j to be ready.
    
    Args:
        max_retries: Maximum number of connection attempts
        delay: Delay in seconds between retries
    
    Raises:
        Exception: If Neo4j is not ready after max_retries
    """
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "neo4jpassword")
    
    print("Waiting for Neo4j to be ready...")
    for attempt in range(max_retries):
        try:
            driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
            with driver.session() as session:
                session.run("RETURN 1")
            driver.close()
            print("✓ Neo4j is ready!")
            return
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"  Attempt {attempt + 1}/{max_retries}: Neo4j not ready yet, retrying in {delay}s...")
                time.sleep(delay)
            else:
                raise Exception(f"Neo4j not ready after {max_retries} attempts") from e


def run_cypher(driver: GraphDatabase.driver, query: str, parameters: Dict[str, Any] = None) -> List[Dict]:
    """
    Executes a single Cypher query.
    
    Args:
        driver: Neo4j driver instance
        query: Cypher query string
        parameters: Optional parameters for the query
    
    Returns:
        List of result records as dictionaries
    """
    with driver.session() as session:
        result = session.run(query, parameters or {})
        return [dict(record) for record in result]


def run_cypher_file(driver: GraphDatabase.driver, file_path: Path) -> None:
    """
    Executes multiple Cypher statements from a file.
    
    Args:
        driver: Neo4j driver instance
        file_path: Path to the .cypher file
    """
    if not file_path.exists():
        print(f"Warning: Cypher file not found at {file_path}")
        return
    
    print(f"Executing Cypher file: {file_path}")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Split by semicolons and filter out empty statements
    statements = [stmt.strip() for stmt in content.split(';') if stmt.strip()]
    
    with driver.session() as session:
        for i, statement in enumerate(statements, 1):
            try:
                session.run(statement)
                print(f"  ✓ Executed statement {i}/{len(statements)}")
            except Exception as e:
                print(f"  ✗ Error in statement {i}: {e}")
                raise


def chunk(dataframe: pd.DataFrame, chunk_size: int = 1000) -> Iterator[pd.DataFrame]:
    """
    Splits a DataFrame into smaller chunks for batch processing.
    
    Args:
        dataframe: The DataFrame to split
        chunk_size: Number of rows per chunk
    
    Yields:
        DataFrame chunks
    """
    for start in range(0, len(dataframe), chunk_size):
        yield dataframe.iloc[start:start + chunk_size]