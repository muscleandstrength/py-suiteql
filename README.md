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

### Interactive Mode

Run without arguments to start the interactive REPL:

```bash
uv run suiteql.py
```

Features:
- SQL syntax highlighting
- Multiline editing — **Alt+Enter** to execute, **Enter** for newline
- Persistent history (`~/.suiteql_history`)
- Ghost-text suggestions from history
- Open query in `$EDITOR` with **Ctrl+X, E**
- Rich table output with pagination info
- Spinner while queries run

### Meta-Commands

| Command | Action |
|---------|--------|
| `\q` | Quit |
| `\f <file>` | Load and execute SQL from a file |
| `\j` | Toggle JSON/table output |
| `\fmt` | Format last query with sqlparse |
| `\l <n>` | Set default LIMIT (`\l` to clear) |
| `\o <n>` | Set default OFFSET (`\o` to clear) |
| `\n` | Next page |
| `\p` | Previous page |
| `\h` | Show help |

### Piped Mode

Pipe a SuiteQL query via stdin:

```bash
echo "SELECT id, companyname FROM customer FETCH FIRST 10 ROWS ONLY" | uv run suiteql.py
```

### File Mode

Pass a SQL file as a positional argument:

```bash
uv run suiteql.py query.sql
```

### Options

- `--limit` — Number of results to return
- `--offset` — Number of results to skip (for pagination)
- `--json` — Output compact JSON (no indentation)
- `-i`, `--interactive` — Force interactive mode

```bash
echo "SELECT id, companyname FROM customer" | uv run suiteql.py --limit 5 --offset 10
```

## Output

- **Interactive mode**: Rich tables by default, toggle to JSON with `\j`
- **Piped/file mode**: JSON to stdout, status messages to stderr
