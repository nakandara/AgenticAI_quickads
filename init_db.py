from pymongo import MongoClient
from datetime import datetime
import uuid

# MongoDB Atlas connection string
MONGO_URI = "mongodb+srv://pramodporuwa:pramod1997@cluster0.wv31aky.mongodb.net/gender?retryWrites=true&w=majority"
DB_NAME = "gender"

def init_db():
    try:
        # Connect to MongoDB
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        print("✅ Connected to MongoDB Atlas successfully!")

        # Sample Users
        users = [
            {
                "userId": str(uuid.uuid4()),
                "name": "John Doe",
                "email": "john@example.com",
                "method": "email",
                "createdAt": datetime.now()
            },
            {
                "userId": str(uuid.uuid4()),
                "name": "Jane Smith",
                "email": "jane@example.com",
                "method": "email",
                "createdAt": datetime.now()
            }
        ]
        
        # Insert Users
        result = db.users.insert_many(users)
        print(f"✅ Added {len(result.inserted_ids)} users")

        # Sample Posts
        posts = [
            {
                "postId": str(uuid.uuid4()),
                "userId": users[0]["userId"],
                "brand": "Toyota",
                "model": "Corolla",
                "title": "Toyota Corolla 2019 for sale",
                "price": "5,500,000",
                "condition": "Used",
                "city": "Colombo",
                "description": "Well maintained Toyota Corolla 2019 model for sale. Single owner, full service history.",
                "mobileNumber": "0771234567",
                "whatsappNumber": "0771234567",
                "yearOfManufacture": "2019",
                "mileage": "45000",
                "engineCapacity": "1800",
                "bodyType": "Sedan",
                "fuelType": ["Petrol"],
                "transmission": ["Automatic"],
                "category": ["Cars"],
                "verify": True,
                "createdAt": datetime.now()
            },
            {
                "postId": str(uuid.uuid4()),
                "userId": users[1]["userId"],
                "brand": "Honda",
                "model": "Civic",
                "title": "Honda Civic 2020 for sale",
                "price": "6,800,000",
                "condition": "Used",
                "city": "Kandy",
                "description": "Honda Civic 2020 in excellent condition. All original parts, accident-free.",
                "mobileNumber": "0777654321",
                "whatsappNumber": "0777654321",
                "yearOfManufacture": "2020",
                "mileage": "35000",
                "engineCapacity": "1500",
                "bodyType": "Sedan",
                "fuelType": ["Petrol"],
                "transmission": ["Automatic"],
                "category": ["Cars"],
                "verify": True,
                "createdAt": datetime.now()
            }
        ]

        # Insert Posts
        result = db.posts.insert_many(posts)
        print(f"✅ Added {len(result.inserted_ids)} posts")

        # Sample Profile
        profile = {
            "userId": users[0]["userId"],
            "username": "johndoe",
            "phoneNumber": "0771234567",
            "city": "Colombo",
            "country": "Sri Lanka",
            "state": "Western",
            "email": "john@example.com",
            "address": "123 Main St, Colombo",
            "status": "Active",
            "avatarUrl": "https://example.com/avatar.jpg",
            "isVerified": True
        }

        # Insert Profile
        result = db.profiles.insert_one(profile)
        print("✅ Added 1 profile")

        print("\n✅ Database initialized successfully!")
        
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    init_db() 