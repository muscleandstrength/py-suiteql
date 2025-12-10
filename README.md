# py-suiteql

Execute SuiteQL queries against NetSuite from Python using the REST API.

## Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) package manager
- NetSuite account with REST API access and OAuth 1.0 credentials

## Setup

1. Clone the repository and navigate to the project directory:

```bash
cd py-suiteql
```

2. Install dependencies using uv:

```bash
uv sync
```

3. Copy the environment template and configure your NetSuite credentials:

```bash
cp .env.dist .env
```

4. Edit `.env` with your NetSuite OAuth credentials:

```
NETSUITE_ACCOUNT_ID="your-account-id"
NETSUITE_CONSUMER_KEY="your-consumer-key"
NETSUITE_CONSUMER_SECRET="your-consumer-secret"
NETSUITE_TOKEN="your-token"
NETSUITE_TOKEN_SECRET="your-token-secret"
```

## Usage

Pipe a SuiteQL query to the script via stdin:

```bash
echo "SELECT id, companyname FROM customer FETCH FIRST 10 ROWS ONLY" | uv run suiteql.py
```

### Options

- `--limit`: Number of results to return
- `--offset`: Number of results to skip (for pagination)

```bash
echo "SELECT id, companyname FROM customer" | uv run suiteql.py --limit 5 --offset 10
```

## Output

Results are returned as JSON to stdout. Status messages are written to stderr.
