from pymongo import MongoClient
import os

client = MongoClient(
  os.environ["DB_HOST"],
  username=os.environ["DB_USER"],
  password=os.environ["DB_PASSWORD"],
  authSource=os.environ["DB_AUTH_SOURCE"]
)

if os.environ["FLASK_ENV"] == "production":
  db = client.production
else:
  db = client.development




