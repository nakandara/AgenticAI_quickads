import os
import sys
from neo4j import GraphDatabase
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Configuration
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# MongoDB Atlas connection string
MONGO_URI = "mongodb+srv://pramodporuwa:pramod1997@cluster0.wv31aky.mongodb.net/gender?retryWrites=true&w=majority"
DB_NAME = "gender"

# Initialize MongoDB connection
try:
    client = MongoClient(MONGO_URI)
    client.admin.command('ping')
    print("✅ MongoDB Atlas සම්බන්ධතාවය සාර්ථකයි!")
    db = client[DB_NAME]
except Exception as e:
    print(f"❌ MongoDB Atlas සම්බන්ධතාවය අසාර්ථකයි: {str(e)}")
    sys.exit(1)

class Neo4jConnection:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
            max_connection_lifetime=30,
            connection_timeout=10
        )
    
    def execute_query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return list(result)

def build_graph():
    print("Initializing Neo4j connection to AuraDB...")
    neo4j = Neo4jConnection()
    
    # Test connection
    try:
        test_query = "RETURN 1 AS test_value"
        result = neo4j.execute_query(test_query)
        if result and result[0]['test_value'] == 1:
            print("✓ Neo4j connection successful")
        else:
            raise ConnectionError("Neo4j connection test failed")
    except Exception as e:
        print(f"Failed to connect to Neo4j AuraDB: {str(e)}")
        return None

    # Clear existing data
    print("Clearing existing graph data...")
    neo4j.execute_query("MATCH (n) DETACH DELETE n")
    
    # Create Users
    print("Loading users...")
    users = {}
    user_count = db['users'].count_documents({})
    print(f"Found {user_count} users to load")
    
    for user in db['users'].find():
        query = """
        CREATE (u:User {
            userId: $userId,
            name: $name,
            email: $email,
            method: $method
        })
        RETURN id(u) as id
        """
        try:
            result = neo4j.execute_query(query, {
                "userId": str(user.get('userId', user.get('_id'))),
                "name": user.get('name', 'Unknown'),
                "email": user.get('email', ''),
                "method": user.get('method', '')
            })
            if result:
                users[str(user.get('_id'))] = result[0]['id']
        except Exception as e:
            print(f"Error creating user {user.get('email')}: {str(e)}")
    
    # Create Posts
    print("\nLoading posts...")
    posts = {}
    post_count = db['posts'].count_documents({})
    print(f"Found {post_count} posts to load")
    
    for post in db['posts'].find():
        query = """
        CREATE (p:Post {
            postId: $postId,
            brand: $brand,
            model: $model,
            title: $title,
            price: $price,
            condition: $condition,
            city: $city,
            description: $description,
            mobileNumber: $mobileNumber,
            whatsappNumber: $whatsappNumber,
            yearOfManufacture: $yearOfManufacture,
            mileage: $mileage,
            engineCapacity: $engineCapacity,
            bodyType: $bodyType,
            fuelType: $fuelType,
            transmission: $transmission,
            category: $category,
            verify: $verify,
            createdAt: datetime($createdAt)
        })
        RETURN id(p) as id
        """
        try:
            result = neo4j.execute_query(query, {
                "postId": str(post.get('postId', post.get('_id'))),
                "brand": post.get('brand', ''),
                "model": post.get('model', ''),
                "title": post.get('title', ''),
                "price": post.get('price', ''),
                "condition": post.get('condition', ''),
                "city": post.get('city', ''),
                "description": post.get('description', ''),
                "mobileNumber": post.get('mobileNumber', ''),
                "whatsappNumber": post.get('whatsappNumber', ''),
                "yearOfManufacture": post.get('yearOfManufacture', ''),
                "mileage": post.get('mileage', ''),
                "engineCapacity": post.get('engineCapacity', ''),
                "bodyType": post.get('bodyType', ''),
                "fuelType": ','.join(post.get('fuelType', [])),
                "transmission": ','.join(post.get('transmission', [])),
                "category": ','.join(post.get('category', [])),
                "verify": post.get('verify', False),
                "createdAt": post.get('createdAt', datetime.now()).isoformat()
            })
            if result:
                posts[str(post.get('_id'))] = result[0]['id']
                
                # Create POSTED relationship
                if post.get('userId'):
                    post_rel_query = """
                    MATCH (u:User {userId: $userId})
                    MATCH (p:Post {postId: $postId})
                    CREATE (u)-[r:POSTED {timestamp: datetime($timestamp)}]->(p)
                    """
                    neo4j.execute_query(post_rel_query, {
                        "userId": str(post.get('userId')),
                        "postId": str(post.get('postId', post.get('_id'))),
                        "timestamp": post.get('createdAt', datetime.now()).isoformat()
                    })
        except Exception as e:
            print(f"Error creating post {post.get('_id')}: {str(e)}")
    
    # Create Profiles
    print("\nLoading profiles...")
    for profile in db['profiles'].find():
        try:
            profile_query = """
            MATCH (u:User {userId: $userId})
            CREATE (p:Profile {
                userId: $userId,
                username: $username,
                phoneNumber: $phoneNumber,
                city: $city,
                country: $country,
                state: $state,
                email: $email,
                address: $address,
                status: $status,
                avatarUrl: $avatarUrl,
                isVerified: $isVerified
            })
            CREATE (u)-[r:HAS_PROFILE]->(p)
            """
            neo4j.execute_query(profile_query, {
                "userId": str(profile.get('userId')),
                "username": profile.get('username', ''),
                "phoneNumber": profile.get('phoneNumber', ''),
                "city": profile.get('city', ''),
                "country": profile.get('country', ''),
                "state": profile.get('state', ''),
                "email": profile.get('email', ''),
                "address": profile.get('address', ''),
                "status": profile.get('status', ''),
                "avatarUrl": profile.get('avatarUrl', ''),
                "isVerified": profile.get('isVerified', False)
            })
        except Exception as e:
            print(f"Error creating profile for user {profile.get('userId')}: {str(e)}")
    
    # Create Saved relationships
    print("\nCreating saved relationships...")
    for save in db['saves'].find():
        if save.get('isSaved'):  # Only create relationship if post is saved
            try:
                save_query = """
                MATCH (u:User {userId: $userId})
                MATCH (p:Post {postId: $postId})
                CREATE (u)-[r:SAVED {timestamp: datetime()}]->(p)
                """
                neo4j.execute_query(save_query, {
                    "userId": str(save.get('userId')),
                    "postId": str(save.get('postId'))
                })
            except Exception as e:
                print(f"Error creating save relationship: {str(e)}")
    
    # Create Reactions
    print("\nCreating reaction relationships...")
    for reaction in db['reactions'].find():
        try:
            reaction_query = """
            MATCH (u:User {userId: $userId})
            MATCH (p:Post {postId: $postId})
            CREATE (u)-[r:REACTED_TO {type: $type, timestamp: datetime()}]->(p)
            """
            neo4j.execute_query(reaction_query, {
                "userId": str(reaction.get('userId')),
                "postId": str(reaction.get('postId')),
                "type": reaction.get('type', 'like')
            })
        except Exception as e:
            print(f"Error creating reaction relationship: {str(e)}")
    
    print("\nGraph build completed successfully!")
    print(f"Created: {len(users)} users, {len(posts)} posts")
    return neo4j

if __name__ == "__main__":
    build_graph()