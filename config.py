#config.py
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# MongoDB Atlas Config
MONGO_URI = "mongodb+srv://pramodporuwa:pramod1997@cluster0.wv31aky.mongodb.net/gender?retryWrites=true&w=majority"
DB_NAME = "gender"

try:
    # Connect to MongoDB Atlas
    client = MongoClient(MONGO_URI)
    # Test the connection
    client.admin.command('ping')
    print("✅ Connected to MongoDB Atlas successfully!")
    
    # Get database handle
    db = client[DB_NAME]
    
    # Test collections
    posts_count = db.posts.count_documents({})
    users_count = db.users.count_documents({})
    profiles_count = db.profiles.count_documents({})
    print(f"Found {posts_count} posts, {users_count} users, and {profiles_count} profiles")
    
except Exception as e:
    print(f"❌ Error connecting to MongoDB Atlas: {str(e)}")
    raise

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("⚠️ Warning: GEMINI_API_KEY not found in environment variables")

# Neo4j Config
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://8dc81e3f.databases.neo4j.io")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "Q5FOyKHFwCQTGq7uIzZ5Ipdd3Up1o7uLW3e6uDLxngM")