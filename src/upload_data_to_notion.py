from notiondbrs import NotionClient
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()

NOTION_TOKEN = os.environ.get("NOTION_TOKEN") or "none"
DB_ID = os.environ.get("DB_ID") or "none"
PAGE_ID = os.environ.get("PAGE_ID") or "none"

client = NotionClient(NOTION_TOKEN)
databases = client.get_all_databases()
print(databases)

data = pd.read_csv("data/job_applications.csv")

df = pd.read_csv("data/job_applications.csv")

df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

upload_data: dict[str, list[str]] = {
    col: df[col].astype(str).tolist()
    for col in df.columns
}

# #client.insert_data(upload_data, DB_ID)
client.insert_data(upload_data, PAGE_ID, new_db=True)