from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

# Neo4j schema definitions
CONSTRAINTS = [
    "CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.userId IS UNIQUE",
    "CREATE CONSTRAINT post_id IF NOT EXISTS FOR (p:Post) REQUIRE p.postId IS UNIQUE",
]

# Node labels and their properties
NODE_SCHEMAS = {
    "User": {
        "properties": [
            "userId",
            "name",
            "email"
        ]
    },
    "Post": {
        "properties": [
            "postId",
            "brand",
            "model",
            "trimEdition",
            "yearOfManufacture",
            "mileage",
            "engineCapacity",
            "fuelType",
            "transmission",
            "bodyType",
            "category",
            "negotiable",
            "description",
            "title",
            "city",
            "price",
            "condition"
        ]
    },
    "Profile": {
        "properties": [
            "userId",
            "username",
            "city",
            "country",
            "email"
        ]
    }
}

# Relationship types and their properties
RELATIONSHIP_SCHEMAS = {
    "POSTED": {
        "from": "User",
        "to": "Post",
        "properties": ["timestamp"]
    },
    "SAVED": {
        "from": "User",
        "to": "Post",
        "properties": ["timestamp"]
    },
    "HAS_PROFILE": {
        "from": "User",
        "to": "Profile",
        "properties": []
    },
    "REACTED_TO": {
        "from": "User",
        "to": "Post",
        "properties": ["type", "timestamp"]
    }
}

def initialize_schema(uri, user, password):
    """Initialize Neo4j schema with constraints and indexes"""
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    with driver.session() as session:
        print("Initializing Neo4j schema...")
        
        # Create constraints
        for constraint in CONSTRAINTS:
            try:
                session.run(constraint)
                print(f"✓ Created constraint: {constraint}")
            except Exception as e:
                print(f"! Error creating constraint: {str(e)}")
        
        print("\nSchema initialization completed!")