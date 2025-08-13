from pymongo import MongoClient
import os 
from dotenv import load_dotenv
import certifi


load_dotenv()

client = MongoClient(os.getenv('MONGO_URI'), tlsCAFile=certifi.where())
db = client.get_database(os.getenv('DB_NAME'))
# print(client.list_database_names())


