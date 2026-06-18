import argparse
import csv
import hashlib
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from azure.data.tables import TableServiceClient, TableTransactionError
from azure.identity import AzureCliCredential, ClientSecretCredential
from dotenv import load_dotenv

load_dotenv()

STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
DEFAULT_TABLE_NAME = os.getenv("AZURE_TABLE_NAME")
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
UPLOAD_DIR = Path(__file__).parent / "upload_files"
BATCH_SIZE = 100  # Azure Tables max per transaction
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "10"))


def sanitize_table_name(name: str) -> str:
    """Azure table names: alphanumeric only, 3-63 chars, cannot start with a digit."""
    sanitized = "".join(c for c in name if c.isalnum())
    if sanitized and sanitized[0].isdigit():
        sanitized = "t" + sanitized
    return sanitized[:63] or "defaulttable"


def sanitize_property_name(name: str) -> str:
    """Azure Table property names: alphanumeric and underscores only."""
    sanitized = "".join(
        c if c.isalnum() or c == "_" else "_" for c in name.strip().strip("'\"")
    )
    if sanitized and sanitized[0].isdigit():
        sanitized = "_" + sanitized
    return sanitized or "Column"


def submit_batch(table_client, batch: list[dict]) -> int:
    """Submit a single batch transaction. Returns number of entities uploaded."""
    operations = [("upsert", entity) for entity in batch]
    try:
        table_client.submit_transaction(operations)
    except TableTransactionError as e:
        print(f"  Batch error: {e}")
        raise
    return len(batch)


def upload_csv(service_client: TableServiceClient, csv_path: Path) -> None:
    table_name = DEFAULT_TABLE_NAME or sanitize_table_name(csv_path.stem)
    print(f"\n--- {csv_path.name} → table '{table_name}' ---")

    table_client = service_client.create_table_if_not_exists(table_name)

    # Read all rows and group into batches
    batches: list[list[dict]] = []
    current_batch: list[dict] = []

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entity = {
                "PartitionKey": table_name,
                "RowKey": hashlib.sha256(
                    "|".join(f"{k}={v}" for k, v in sorted(row.items()) if k).encode()
                ).hexdigest(),
            }
            entity.update(
                {
                    sanitize_property_name(k): v.strip().strip("'\"")
                    for k, v in row.items()
                    if k
                }
            )
            current_batch.append(entity)

            if len(current_batch) >= BATCH_SIZE:
                batches.append(current_batch)
                current_batch = []

    if current_batch:
        batches.append(current_batch)

    total_rows = sum(len(b) for b in batches)
    total_batches = len(batches)
    print(
        f"  {total_rows} rows in {total_batches} batch(es), uploading with {MAX_WORKERS} threads..."
    )

    uploaded = 0
    completed_batches = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(submit_batch, table_client, batch): i
            for i, batch in enumerate(batches)
        }
        for future in as_completed(futures):
            uploaded += future.result()
            completed_batches += 1
            pct = (uploaded / total_rows) * 100
            print(
                f"\r  Progress: {uploaded}/{total_rows} rows ({pct:.1f}%) - batch {completed_batches}/{total_batches}",
                end="",
                flush=True,
            )

    print(f"\n  Done: {uploaded} rows uploaded.")

    print(f"  Uploaded {uploaded} rows.")


def main() -> None:
    if not STORAGE_ACCOUNT_NAME:
        raise SystemExit("Error: AZURE_STORAGE_ACCOUNT_NAME is not set in .env")

    parser = argparse.ArgumentParser(description="Upload CSVs to Azure Tables")
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Use Azure CLI credentials (az login) instead of service account from .env",
    )
    args = parser.parse_args()

    csv_files = sorted(UPLOAD_DIR.glob("*.csv"))
    if not csv_files:
        raise SystemExit(f"No CSV files found in {UPLOAD_DIR}")

    print(f"Found {len(csv_files)} CSV file(s) in {UPLOAD_DIR}")

    account_url = f"https://{STORAGE_ACCOUNT_NAME}.table.core.windows.net"
    if args.cli:
        credential = AzureCliCredential()
    else:
        credential = ClientSecretCredential(AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET)
    service_client = TableServiceClient(endpoint=account_url, credential=credential)

    for csv_path in csv_files:
        upload_csv(service_client, csv_path)

    print("\nDone!")


if __name__ == "__main__":
    main()
