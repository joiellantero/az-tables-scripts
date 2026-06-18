# Azure Table Scripts

## Setup before running the scripts
1. create a virtual environment to store your dependencies by running `python -m venv venv`
2. activate the virtual environment by running `source venv/bin/activate`
3. install the dependencies using `pip install -r requirements.txt`.
4. set the environment variables in a `.env` file (see **Credentials** below).
5. choose a script to run.

## Credentials

Two authentication modes are supported.

### Option A — Service Account (default)
Add the following to your `.env`:
```env
AZURE_STORAGE_ACCOUNT_NAME=your-storage-account
AZURE_TABLE_NAME=your-table-name
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
```
No extra flag needed — service account is used by default.

### Option B — Azure CLI (`az login`)
Only `AZURE_STORAGE_ACCOUNT_NAME` (and optionally `AZURE_TABLE_NAME`) are needed in `.env`. Pass `--cli` when running:
```env
AZURE_STORAGE_ACCOUNT_NAME=your-storage-account
AZURE_TABLE_NAME=your-table-name
```
```shell
python upload.py --cli
python view.py --cli
```

## Upload CSV Files
1. create upload_files folder then put your CSV files in it. 

    Sample csv: 
    ```csv
    PartitionKey,RowKey,Data
    2026-06-18T00:00:00Z,00000000-0000-0000-0000-000000000000,example.domain.com
    ```

2. `python upload.py` — uses service account from `.env`
3. `python upload.py --cli` — uses `az login` credentials
4. wait for the upload to complete -- the script has live progress update.

## View Azure Table Storage Content
```shell
# Show 10 rows (default) — service account
python view.py

# Show 10 rows — az login
python view.py --cli

# Show 50 rows
python view.py -n 50

# Specify a different table
python view.py -t myothertable -n 20
```
