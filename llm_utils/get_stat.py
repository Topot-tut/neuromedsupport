from langsmith import Client
from datetime import datetime, timedelta
import pandas as pd

from config import LANGCHAIN_KEY

client = Client(api_key=LANGCHAIN_KEY)



email = {}


total_llm_runs = client.list_runs(
    project_name="test",
    start_time=datetime.now() - timedelta(days=1),
    is_root=True
)

for item in total_llm_runs:
    print(item)

