"""Pytest configuration and fixtures for Quack MCP tests."""

import asyncio
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Dict, Generator

import pytest
import duckdb
from quack_mcp.server import QuackMCPServer


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def server() -> AsyncGenerator[QuackMCPServer, None]:
    """Create a QuackMCP server instance for testing."""
    server_instance = QuackMCPServer()
    yield server_instance
    # Cleanup: close database connection if exists
    if server_instance.db:
        server_instance.db.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_csv_data() -> Dict[str, str]:
    """Sample CSV data for testing."""
    return {
        "employees": """name,age,department,salary
John Doe,30,Engineering,75000
Jane Smith,25,Marketing,65000
Bob Johnson,35,Engineering,80000
Alice Brown,28,Sales,60000
Charlie Wilson,32,Marketing,70000""",
        
        "sales": """date,product,quantity,price
2024-01-01,Widget A,10,25.50
2024-01-02,Widget B,5,45.00
2024-01-03,Widget A,8,25.50
2024-01-04,Widget C,12,35.75
2024-01-05,Widget B,3,45.00""",
        
        "expenses": """Date,Name,Amount
2024-01-01,STARBUCKS COFFEE,-4.50
2024-01-02,GROCERY STORE,-45.67
2024-01-03,NETFLIX SUBSCRIPTION,-15.99
2024-01-04,RESTAURANT XYZ,-28.75
2024-01-05,GAS STATION,-35.00""",
        
        "inventory": """item_id,name,quantity,cost
1,Widget A,100,20.00
2,Widget B,50,40.00
3,Widget C,75,30.00
4,Widget D,25,50.00
5,Widget E,150,15.00""",
        
        "empty": "name,value\n",  # Empty CSV with headers only
        
        "malformed": """name,age,department
John,30,Engineering
Jane,25  # Missing department
Bob,35,Engineering,Extra Field
Alice,28,Sales""",
    }


@pytest.fixture
def sample_excel_data() -> bytes:
    """Sample Excel data for testing (minimal XLSX format)."""
    # This is a minimal valid XLSX file with sample data
    # In a real implementation, you'd create actual Excel files for testing
    return b"Sample Excel data - would be actual XLSX binary in production"


@pytest.fixture
def create_csv_file(temp_dir: Path, sample_csv_data: Dict[str, str]):
    """Factory fixture to create CSV files in temp directory."""
    def _create_csv_file(name: str, data_key: str = None) -> Path:
        """Create a CSV file with given name and data."""
        if data_key is None:
            data_key = name
        
        csv_path = temp_dir / f"{name}.csv"
        csv_path.write_text(sample_csv_data.get(data_key, sample_csv_data["employees"]))
        return csv_path
    
    return _create_csv_file


@pytest.fixture
def create_multiple_csv_files(temp_dir: Path, sample_csv_data: Dict[str, str]):
    """Create multiple CSV files for multi-file testing."""
    files = {}
    for name, data in sample_csv_data.items():
        if name not in ["empty", "malformed"]:  # Skip problematic files for multi-file tests
            csv_path = temp_dir / f"{name}.csv"
            csv_path.write_text(data)
            files[name] = csv_path
    return files


@pytest.fixture
def create_nested_csv_files(temp_dir: Path, sample_csv_data: Dict[str, str]):
    """Create nested directory structure with CSV files."""
    # Create subdirectories
    reports_dir = temp_dir / "reports" / "2024"
    reports_dir.mkdir(parents=True)
    
    data_dir = temp_dir / "data"
    data_dir.mkdir()
    
    # Create files in different directories
    files = {
        "root_sales": temp_dir / "sales_q1.csv",
        "root_employees": temp_dir / "employees_dept1.csv",
        "reports_jan": reports_dir / "monthly_jan.csv",
        "reports_feb": reports_dir / "monthly_feb.csv",
        "data_inventory": data_dir / "inventory_jan.csv",
    }
    
    # Use different sample data for variety
    data_mapping = {
        "root_sales": "sales",
        "root_employees": "employees",
        "reports_jan": "sales",
        "reports_feb": "expenses",
        "data_inventory": "inventory",
    }
    
    for key, path in files.items():
        data_key = data_mapping[key]
        path.write_text(sample_csv_data[data_key])
    
    return files


@pytest.fixture
async def loaded_test_table(server: QuackMCPServer, create_csv_file) -> str:
    """Create and load a test table for analysis testing."""
    csv_file = create_csv_file("test_employees", "employees")
    
    # Load the CSV manually for testing
    query = f"""
        CREATE OR REPLACE TABLE "test_employees" AS 
        SELECT * FROM read_csv('{csv_file}', header=true)
    """
    await server.execute_query(query)
    server.add_loaded_table("test_employees", str(csv_file))
    
    return "test_employees"


@pytest.fixture
async def loaded_expense_table(server: QuackMCPServer, create_csv_file) -> str:
    """Create and load an expense table for optimization testing."""
    csv_file = create_csv_file("test_expenses", "expenses")
    
    # Load the CSV manually for testing
    query = f"""
        CREATE OR REPLACE TABLE "test_expenses" AS 
        SELECT * FROM read_csv('{csv_file}', header=true)
    """
    await server.execute_query(query)
    server.add_loaded_table("test_expenses", str(csv_file))
    
    return "test_expenses"


@pytest.fixture
def mock_duckdb_connection():
    """Mock DuckDB connection for unit tests."""
    class MockConnection:
        def __init__(self):
            self.queries = []
            self.description = [("column1",), ("column2",)]
            self.results = []
        
        def execute(self, query: str):
            self.queries.append(query)
            return self
        
        def fetchall(self):
            return self.results
        
        def close(self):
            pass
    
    return MockConnection()


@pytest.fixture
def sample_schema():
    """Sample table schema for testing."""
    return [
        {"column_name": "id", "column_type": "INTEGER", "null": "NO"},
        {"column_name": "name", "column_type": "VARCHAR", "null": "YES"},
        {"column_name": "amount", "column_type": "DOUBLE", "null": "YES"},
        {"column_name": "date", "column_type": "DATE", "null": "YES"},
    ]


@pytest.fixture
def sample_query_result():
    """Sample query result data for testing."""
    return [
        {"id": 1, "name": "John", "amount": 100.50, "date": "2024-01-01"},
        {"id": 2, "name": "Jane", "amount": 200.75, "date": "2024-01-02"},
        {"id": 3, "name": "Bob", "amount": 150.25, "date": "2024-01-03"},
    ]


# Markers for different types of tests
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "file_io: marks tests that require file I/O"
    )