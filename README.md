# Unstract API Hub Python Client

A Python client for the Unstract ApiHub service that provides a clean, Pythonic interface for document processing APIs following the extract → status → retrieve pattern.

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/Zipstack/apihub-python-client)
[![PyPI Downloads](https://img.shields.io/pypi/dm/apihub-python-client)](https://pypi.org/project/apihub-python-client/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## 🚀 Features

- **Simple API Interface**: Clean, easy-to-use client for Unstract ApiHub services
- **File Processing**: Support for document processing with file uploads
- **Status Monitoring**: Track processing status with polling capabilities
- **Error Handling**: Comprehensive exception handling with meaningful messages
- **Flexible Parameters**: Support for custom parameters and configurations
- **Automatic Polling**: Optional wait-for-completion functionality
- **Type Safety**: Full type hints for better development experience

## 📦 Installation

```bash
pip install apihub-python-client
```

Or install from source:

```bash
git clone https://github.com/Zipstack/apihub-python-client.git
cd apihub-python-client
pip install -e .
```

## 🎯 Quick Start

### Basic Usage

```python
from apihub_client import ApiHubClient

# Initialize the client
client = ApiHubClient(
    api_key="your-api-key-here",
    base_url="https://api-hub.us-central.unstract.com/api/v1"
)

# Process a document with automatic completion waiting
result = client.extract(
    endpoint="bank_statement",
    vertical="table",
    sub_vertical="bank_statement",
    file_path="statement.pdf",
    wait_for_completion=True,
    polling_interval=3  # Check status every 3 seconds
)

print("Processing completed!")
print(result)
```

## 🛠️ Common Use Cases

### All Table Extraction API

```python

    # Step 1: Discover tables from the uploaded PDF
    initial_result = client.extract(
        endpoint="discover_tables",
        vertical="table",
        sub_vertical="discover_tables",
        ext_cache_result="true",
        ext_cache_text="true",
        file_path="statement.pdf"
    )
    file_hash = initial_result.get("file_hash")
    print("File hash", file_hash)
    discover_tables_result = client.wait_for_complete(file_hash,
        timeout=600, # max wait for 10 mins
        polling_interval=3 # polling every 3s
    )

    tables = json.loads(discover_tables_result['data'])
    print(f"Total tables in this document: {len(tables)}")

    all_table_result = []
    # Step 2: Extract specific table
    for i, table in enumerate(tables):
        table_result = client.extract(
            endpoint="extract_table",
            vertical="table",
            sub_vertical="extract_table",
            file_hash=file_hash,
            ext_table_no=i, # extracting nth table
            wait_for_completion=True
        )

        print(f"Extracted table : {table['table_name']}")
        all_table_result.append({table["table_name"]: table_result})

    print("All table result")
    print(all_table_result)

```

### Bank Statement Extraction API

```python
# Process bank statement
result = client.extract(
    endpoint="bank_statement",
    vertical="table",
    sub_vertical="bank_statement",
    file_path="bank_statement.pdf",
    wait_for_completion=True,
    polling_interval=3
)

print("Bank statement processed:", result)
```

### Step-by-Step Processing

```python
# Step 1: Start processing
initial_result = client.extract(
    endpoint="discover_tables",
    vertical="table",
    sub_vertical="discover_tables",
    file_path="document.pdf"
)

file_hash = initial_result["file_hash"]
print(f"Processing started with hash: {file_hash}")

# Step 2: Monitor status
status = client.get_status(file_hash)
print(f"Current status: {status['status']}")

# Step 3: Wait for completion (using wait_for_complete method)
final_result = client.wait_for_complete(
    file_hash=file_hash,
    timeout=600,        # Wait up to 10 minutes
    polling_interval=3  # Check every 3 seconds
)
print("Final result:", final_result)

```

### Using Cached Files

Once a file has been processed, you can reuse it by file hash:

```python
# Process a different operation on the same file
table_result = client.extract(
    endpoint="extract_table",
    vertical="table",
    sub_vertical="extract_table",
    file_hash="previously-obtained-hash",
    ext_table_no=1,  # Extract second table. Indexing starts at 0
    wait_for_completion=True
)
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file:

```bash
API_KEY=your_api_key_here
BASE_URL=https://api.example.com
LOG_LEVEL=INFO
```

Then load in your code:

```python
import os
from dotenv import load_dotenv
from apihub_client import ApiHubClient

load_dotenv()

client = ApiHubClient(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL")
)
```

## 📚 API Reference

### ApiHubClient

The main client class for interacting with the ApiHub service.

```python
client = ApiHubClient(api_key: str, base_url: str)
```

**Parameters:**

- `api_key` (str): Your API key for authentication
- `base_url` (str): The base URL of the ApiHub service

#### Methods

##### extract()

Start a document processing operation.

```python
extract(
    endpoint: str,
    vertical: str,
    sub_vertical: str,
    file_path: str | None = None,
    file_hash: str | None = None,
    wait_for_completion: bool = False,
    polling_interval: int = 5,
    **kwargs
) -> dict
```

**Parameters:**

- `endpoint` (str): The API endpoint to call (e.g., "discover_tables", "extract_table")
- `vertical` (str): The processing vertical
- `sub_vertical` (str): The processing sub-vertical
- `file_path` (str, optional): Path to file for upload (for new files)
- `file_hash` (str, optional): Hash of previously uploaded file (for cached operations)
- `wait_for_completion` (bool): If True, polls until completion and returns final result
- `polling_interval` (int): Seconds between status checks when waiting (default: 5)
- `**kwargs`: Additional parameters specific to the endpoint

**Returns:**

- `dict`: API response containing processing results or file hash for tracking

##### get_status()

Check the status of a processing job.

```python
get_status(file_hash: str) -> dict
```

**Parameters:**

- `file_hash` (str): The file hash returned from extract()

**Returns:**

- `dict`: Status information including current processing state

##### retrieve()

Get the final results of a completed processing job.

```python
retrieve(file_hash: str) -> dict
```

**Parameters:**

- `file_hash` (str): The file hash of the completed job

**Returns:**

- `dict`: Final processing results

##### wait_for_complete()

Wait for a processing job to complete by polling its status.

```python
wait_for_complete(
    file_hash: str,
    timeout: int = 600,
    polling_interval: int = 3
) -> dict
```

**Parameters:**

- `file_hash` (str): The file hash of the job to wait for
- `timeout` (int): Maximum time to wait in seconds (default: 600)
- `polling_interval` (int): Seconds between status checks (default: 3)

**Returns:**

- `dict`: Final processing results when completed

**Raises:**

- `ApiHubClientException`: If processing fails or times out

### Exception Handling

```python
from apihub_client import ApiHubClientException

try:
    result = client.extract(
        endpoint="bank_statement",
        vertical="table",
        sub_vertical="bank_statement",
        file_path="document.pdf"
    )
except ApiHubClientException as e:
    print(f"Error: {e.message}")
    print(f"Status Code: {e.status_code}")
```

### Batch Processing

```python
import time
from pathlib import Path

def process_documents(file_paths, endpoint):
    results = []

    for file_path in file_paths:
        try:
            print(f"Processing {file_path}...")
            # Start processing
            initial_result = client.extract(
                endpoint=endpoint,
                vertical="table",
                sub_vertical=endpoint,
                file_path=file_path
            )

            # Wait for completion with custom settings
            result = client.wait_for_complete(
                file_hash=initial_result["file_hash"],
                timeout=900,        # 15 minutes for batch processing
                polling_interval=5  # Less frequent polling for batch
            )
            results.append({"file": file_path, "result": result, "success": True})

        except ApiHubClientException as e:
            print(f"Failed to process {file_path}: {e.message}")
            results.append({"file": file_path, "error": str(e), "success": False})

    return results

# Process multiple files
file_paths = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
results = process_documents(file_paths, "bank_statement")

# Summary
successful = [r for r in results if r["success"]]
failed = [r for r in results if not r["success"]]

print(f"Processed: {len(successful)} successful, {len(failed)} failed")
```

## 🧪 Testing

Run the test suite:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run tests with coverage
pytest --cov=apihub_client --cov-report=html

# Run specific test files
pytest test/test_client.py -v
pytest test/test_integration.py -v
```

### Integration Testing

For integration tests with a real API:

```bash
# Create .env file with real credentials
cp .env.example .env
# Edit .env with your API credentials

# Run integration tests
pytest test/test_integration.py -v
```

## 🔍 Logging

Enable debug logging to see detailed request/response information:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

client = ApiHubClient(api_key="your-key", base_url="https://api.example.com")

# Now all API calls will show detailed logs
result = client.extract(...)
```

## 🚀 Releases

This project uses automated releases through GitHub Actions with PyPI Trusted Publishers for secure publishing.

### Creating a Release

1. **Go to GitHub Actions** → **"Release Tag and Publish Package"**
2. **Click "Run workflow"** and configure:
   - **Version bump**: `patch` (bug fixes), `minor` (new features), or `major` (breaking changes)
   - **Pre-release**: Check for beta/alpha versions
   - **Release notes**: Optional custom notes
3. **Click "Run workflow"** - the automation handles the rest!

The workflow will automatically:

- Update version in the code
- Create Git tags and GitHub releases
- Run all tests and quality checks
- Publish to PyPI using `uv publish` with Trusted Publishers

For more details, see [Release Documentation](.github/RELEASE.md).

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/Zipstack/apihub-python-client.git
cd apihub-python-client

# Install dependencies using uv (required - do not use pip)
uv sync

# Install pre-commit hooks
uv run --frozen pre-commit install

# Run tests
uv run --frozen pytest

# Run linting and formatting
uv run --frozen ruff check .
uv run --frozen ruff format .

# Run type checking
uv run --frozen mypy src/

# Run all pre-commit hooks manually
uv run --frozen pre-commit run --all-files
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/Zipstack/apihub-python-client/issues)
- **Documentation**: Check this README and inline code documentation
- **Examples**: See the `examples/` directory for more usage patterns

## 📈 Version History

### v0.1.0

- Initial release
- Basic client functionality with extract, status, and retrieve operations
- File upload support
- Automatic polling with wait_for_completion
- Comprehensive test suite

---

Made with ❤️ by the Unstract team
