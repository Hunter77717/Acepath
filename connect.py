from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["QuatitativeAptitude"]
collection = db["aptitude_questions"]
print("Connected to MongoDB")
