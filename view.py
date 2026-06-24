import argparse
import csv
import os

from azure.data.tables import TableServiceClient
from azure.identity import AzureCliCredential, ClientSecretCredential
from dotenv import load_dotenv

load_dotenv()

STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
DEFAULT_TABLE_NAME = os.getenv("AZURE_TABLE_NAME")
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")


def get_credential(use_cli: bool):
    if use_cli:
        return AzureCliCredential()
    return ClientSecretCredential(AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET)


def view_table(table_name: str, rows: int, use_cli: bool, output: str | None = None) -> None:
    account_url = f"https://{STORAGE_ACCOUNT_NAME}.table.core.windows.net"
    credential = get_credential(use_cli)
    service_client = TableServiceClient(endpoint=account_url, credential=credential)
    table_client = service_client.get_table_client(table_name)

    entities = table_client.list_entities(results_per_page=rows)

    # Collect rows up to the limit
    data = []
    for i, entity in enumerate(entities):
        if i >= rows:
            break
        row = {
            k: v
            for k, v in entity.items()
            if k not in ("PartitionKey", "RowKey", "etag")
        }
        data.append(row)

    if not data:
        print(f"Table '{table_name}' is empty.")
        return

    columns = list(data[0].keys())

    if output:
        with open(output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(data)
        print(f"Exported {len(data)} row(s) from '{table_name}' to '{output}'")
        return

    # Build column widths for formatting
    widths = {col: len(col) for col in columns}
    for row in data:
        for col in columns:
            widths[col] = max(widths[col], len(str(row.get(col, ""))))

    # Print header
    header = " | ".join(col.ljust(widths[col]) for col in columns)
    separator = "-+-".join("-" * widths[col] for col in columns)
    print(header)
    print(separator)

    # Print rows
    for row in data:
        line = " | ".join(str(row.get(col, "")).ljust(widths[col]) for col in columns)
        print(line)

    print(f"\nShowing {len(data)} row(s) from '{table_name}'")


def main() -> None:
    if not STORAGE_ACCOUNT_NAME:
        raise SystemExit("Error: AZURE_STORAGE_ACCOUNT_NAME is not set in .env")

    parser = argparse.ArgumentParser(description="View Azure Table contents")
    parser.add_argument(
        "-t",
        "--table",
        default=DEFAULT_TABLE_NAME,
        help=f"Table name (default: {DEFAULT_TABLE_NAME})",
    )
    parser.add_argument(
        "-n",
        "--rows",
        type=int,
        default=10,
        help="Number of rows to display (default: 10)",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Use Azure CLI credentials (az login) instead of service account from .env",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Export results to a CSV file (e.g., -o output.csv)",
    )
    args = parser.parse_args()

    if not args.table:
        raise SystemExit(
            "Error: No table name provided. Use -t or set AZURE_TABLE_NAME in .env"
        )

    view_table(args.table, args.rows, args.cli, args.output)


if __name__ == "__main__":
    main()
