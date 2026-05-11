# Azure Table Scripts

## Setup before running the scripts
1. create a virtual environment to store your dependencies by running `python -m venv venv`
2. activate the virtual environment by running `source venv/bin/activate`
3. install the dependencies using `pip install -r requirements.txt`.
4. set the environment variables `AZURE_STORAGE_ACCOUNT_NAME` and `AZURE_STORAGE_ACCOUNT_KEY` in a .env file
5. choose a script to run.

## Upload CSV Files
1. create upload_files folder then put your CSV files in it. 

    Sample csv: 
    ```csv
    'Name or Address' , 'Policy' , 'Data'
    'cryptocurrency.eicar.network' , 'BlockNxdomainDomain' , ''
    ```

2. `python upload.py`.
3. wait for the upload to complete -- the script has live progress update.

## View Azure Table Storage Content
```shell
# Show 10 rows (default) from table in .env
python view_table.py

# Show 50 rows
python view_table.py -n 50

# Specify a different table
python view_table.py -t myothertable -n 20
```
