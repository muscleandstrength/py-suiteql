#!/usr/bin/env python3

import argparse
import json
import os
import sys

import requests
from dotenv import load_dotenv
from requests_oauthlib import OAuth1

load_dotenv()


def get_args():
    parser = argparse.ArgumentParser(description="Run a SuiteQL query")
    parser.add_argument("file", nargs="?", help="SQL file to execute")
    parser.add_argument("--limit", type=int, help="Number of results to return")
    parser.add_argument("--offset", type=int, help="Number of results to skip")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Output raw JSON")
    parser.add_argument(
        "-i", "--interactive", action="store_true", help="Force interactive mode"
    )
    return parser.parse_args()


def get_credentials():
    account_id = os.getenv("NETSUITE_ACCOUNT_ID")
    consumer_key = os.getenv("NETSUITE_CONSUMER_KEY")
    consumer_secret = os.getenv("NETSUITE_CONSUMER_SECRET")
    token = os.getenv("NETSUITE_TOKEN")
    token_secret = os.getenv("NETSUITE_TOKEN_SECRET")

    required_vars = {
        "NETSUITE_ACCOUNT_ID": account_id,
        "NETSUITE_CONSUMER_KEY": consumer_key,
        "NETSUITE_CONSUMER_SECRET": consumer_secret,
        "NETSUITE_TOKEN": token,
        "NETSUITE_TOKEN_SECRET": token_secret,
    }

    missing_vars = [k for k, v in required_vars.items() if not v]
    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

    return (account_id, consumer_key, consumer_secret, token, token_secret)


def run_suiteql_query(query, limit=None, offset=None):
    (account_id, consumer_key, consumer_secret, token, token_secret) = get_credentials()
    url = f"https://{account_id}.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql"
    params = {}

    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset

    oauth = OAuth1(
        client_key=consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=token,
        resource_owner_secret=token_secret,
        realm=account_id,
        signature_method="HMAC-SHA256",
    )

    headers = {"Content-Type": "application/json", "prefer": "transient"}
    payload = {"q": query}

    response = requests.post(
        url, params=params, auth=oauth, headers=headers, json=payload
    )
    response.raise_for_status()
    return response.json()


def interactive_repl(args):
    from pathlib import Path

    import sqlparse
    from prompt_toolkit import PromptSession
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.lexers import PygmentsLexer
    from pygments.lexers.sql import SqlLexer
    from rich.console import Console
    from rich.json import JSON
    from rich.table import Table

    console = Console()
    history_file = Path.home() / ".suiteql_history"
    session = PromptSession(
        lexer=PygmentsLexer(SqlLexer),
        history=FileHistory(str(history_file)),
        auto_suggest=AutoSuggestFromHistory(),
        multiline=True,
        enable_open_in_editor=True,
    )

    output_json = False
    default_limit = args.limit
    default_offset = args.offset
    last_query = None

    def show_help():
        help_table = Table(title="Meta-Commands", show_header=True)
        help_table.add_column("Command", style="bold cyan")
        help_table.add_column("Action")
        help_table.add_row("\\q", "Quit")
        help_table.add_row("\\f <file>", "Load and execute SQL from a file")
        help_table.add_row("\\j", "Toggle JSON/table output")
        help_table.add_row("\\fmt", "Format last query with sqlparse")
        help_table.add_row("\\l <n>", "Set default LIMIT (\\l to clear)")
        help_table.add_row("\\o <n>", "Set default OFFSET (\\o to clear)")
        help_table.add_row("\\n", "Next page")
        help_table.add_row("\\p", "Previous page")
        help_table.add_row("\\h", "Show this help")
        help_table.add_row("", "")
        help_table.add_row("Alt+Enter", "Execute query")
        help_table.add_row("Ctrl+X, E", "Open in $EDITOR")
        help_table.add_row("Ctrl+D", "Quit")
        console.print(help_table)

    def display_result(result):
        items = result.get("items", [])
        total = result.get("totalResults", 0)
        offset = result.get("offset", 0)
        has_more = result.get("hasMore", False)
        count = result.get("count", len(items))

        if output_json:
            console.print(JSON(json.dumps(result, indent=2)))
        else:
            if not items:
                console.print("[dim]No results.[/dim]")
                return
            table = Table(show_header=True, header_style="bold magenta")
            keys = list(items[0].keys())
            for key in keys:
                table.add_column(key)
            for row in items:
                table.add_row(*[str(row.get(k, "")) for k in keys])
            console.print(table)

        parts = [f"[dim]{count} rows[/dim]"]
        if offset:
            parts.append(f"[dim]offset {offset}[/dim]")
        if total:
            parts.append(f"[dim]{total} total[/dim]")
        if has_more:
            parts.append("[yellow]more available (\\n for next page)[/yellow]")
        console.print(" | ".join(parts))

    def execute_query(query, limit=None, offset=None):
        nonlocal last_query
        last_query = query
        lim = limit if limit is not None else default_limit
        off = offset if offset is not None else default_offset
        with console.status("Running query..."):
            try:
                result = run_suiteql_query(query, lim, off)
            except requests.exceptions.HTTPError as e:
                body = ""
                if e.response is not None:
                    try:
                        body = json.dumps(e.response.json(), indent=2)
                    except Exception:
                        body = e.response.text
                console.print(f"[red]HTTP error: {e}[/red]")
                if body:
                    console.print(body)
                return
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                return
        display_result(result)

    console.print("[bold]SuiteQL Interactive REPL[/bold]")
    console.print("[dim]Type SQL and press Alt+Enter to execute. \\h for help, \\q to quit.[/dim]\n")

    while True:
        try:
            text = session.prompt("suiteql> ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\nBye!")
            break

        if not text:
            continue

        # Meta-commands
        if text == "\\q":
            console.print("Bye!")
            break
        elif text == "\\h":
            show_help()
        elif text == "\\j":
            output_json = not output_json
            mode = "JSON" if output_json else "table"
            console.print(f"Output mode: [bold]{mode}[/bold]")
        elif text.startswith("\\f"):
            parts = text.split(None, 1)
            if len(parts) < 2:
                console.print("[red]Usage: \\f <file>[/red]")
                continue
            filepath = parts[1]
            try:
                query = Path(filepath).read_text().strip()
            except FileNotFoundError:
                console.print(f"[red]File not found: {filepath}[/red]")
                continue
            console.print(f"[dim]Loaded {filepath}[/dim]")
            execute_query(query)
        elif text == "\\fmt":
            if not last_query:
                console.print("[red]No previous query to format.[/red]")
            else:
                formatted = sqlparse.format(
                    last_query, reindent=True, keyword_case="upper"
                )
                console.print(formatted)
        elif text.startswith("\\l"):
            parts = text.split(None, 1)
            if len(parts) < 2:
                default_limit = None
                console.print("Default LIMIT cleared.")
            else:
                try:
                    default_limit = int(parts[1])
                    console.print(f"Default LIMIT: [bold]{default_limit}[/bold]")
                except ValueError:
                    console.print("[red]Usage: \\l <number>[/red]")
        elif text.startswith("\\o"):
            parts = text.split(None, 1)
            if len(parts) < 2:
                default_offset = None
                console.print("Default OFFSET cleared.")
            else:
                try:
                    default_offset = int(parts[1])
                    console.print(f"Default OFFSET: [bold]{default_offset}[/bold]")
                except ValueError:
                    console.print("[red]Usage: \\o <number>[/red]")
        elif text == "\\n":
            if not last_query:
                console.print("[red]No previous query to paginate.[/red]")
            else:
                step = default_limit or 10
                default_offset = (default_offset or 0) + step
                console.print(f"[dim]offset → {default_offset}[/dim]")
                execute_query(last_query)
        elif text == "\\p":
            if not last_query:
                console.print("[red]No previous query to paginate.[/red]")
            else:
                step = default_limit or 10
                default_offset = max((default_offset or 0) - step, 0)
                console.print(f"[dim]offset → {default_offset}[/dim]")
                execute_query(last_query)
        elif text.startswith("\\"):
            console.print(f"[red]Unknown command: {text}[/red]")
        else:
            execute_query(text)


if __name__ == "__main__":
    args = get_args()

    if args.file:
        query = open(args.file).read().strip()
        print("Running query...", file=sys.stderr)
        try:
            result = run_suiteql_query(query, args.limit, args.offset)
        except requests.exceptions.HTTPError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(result, indent=2))
    elif args.interactive or sys.stdin.isatty():
        interactive_repl(args)
    else:
        query = sys.stdin.read().strip()
        print("Running query...", file=sys.stderr)
        try:
            result = run_suiteql_query(query, args.limit, args.offset)
        except requests.exceptions.HTTPError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        if args.json_output:
            print(json.dumps(result))
        else:
            print(json.dumps(result, indent=2))
