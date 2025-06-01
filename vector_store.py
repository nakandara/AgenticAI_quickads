#vector_store.py
import os
from config import db, GEMINI_API_KEY
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from bson import ObjectId

DB_PATH = "faiss_index"
CHUNK_SIZE = 300
CHUNK_OVERLAP = 30

def build_vector_db():
    documents = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

    try:
        # Process posts collection
        posts_collection = db.posts
        print("\nProcessing posts...")
        post_count = 0
        for post in posts_collection.find():
            try:
                # Extract image URLs if they exist
                image_urls = []
                if 'images' in post and isinstance(post['images'], list):
                    image_urls = [img.get('imageUrl', '') for img in post['images'] if isinstance(img, dict)]
                
                # Handle ObjectId fields
                post_id = str(post.get('_id', ''))
                user_id = str(post.get('userId', ''))
                
                text_parts = [
                    f"Title: {post.get('title', '')}",
                    f"Brand: {post.get('brand', '')}",
                    f"Model: {post.get('model', '')}",
                    f"Year: {post.get('yearOfManufacture', '')}",
                    f"Mileage: {post.get('mileage', '')}",
                    f"Engine Capacity: {post.get('engineCapacity', '')}",
                    f"Fuel Type: {post.get('fuelType', '')}",
                    f"Transmission: {post.get('transmission', '')}",
                    f"Body Type: {post.get('bodyType', '')}",
                    f"Category: {', '.join(post.get('category', []) if isinstance(post.get('category'), list) else [str(post.get('category', ''))])}",
                    f"Price: {post.get('price', '')}",
                    f"City: {post.get('city', '')}",
                    f"Condition: {post.get('condition', '')}",
                    f"Mobile: {post.get('mobileNumber', '')}",
                    f"WhatsApp: {post.get('whatsappNumber', '')}",
                    f"Description: {post.get('description', '')}"
                ]
                
                if image_urls:
                    text_parts.append(f"Images: {', '.join(image_urls)}")
                
                # Only include non-empty fields
                text = "\n".join([part for part in text_parts if part.split(': ')[1].strip()])
                
                if text.strip():  # Only add if there's actual content
                    metadata = {
                        "collection": "posts",
                        "post_id": post_id,
                        "user_id": user_id,
                        "title": post.get('title', ''),
                        "source": "mongodb"
                    }
                    documents.append(Document(page_content=text, metadata=metadata))
                    post_count += 1
                    print(f"Added post {post_count}: {post.get('title', '')}")
            except Exception as e:
                print(f"Error processing post: {str(e)}")
                continue

        # Process users collection
        print("\nProcessing users...")
        user_count = 0
        users_collection = db.users
        for user in users_collection.find():
            try:
                # Handle ObjectId
                user_id = str(user.get('_id', ''))
                
                text_parts = [
                    f"Name: {user.get('name', '')}",
                    f"Email: {user.get('email', '')}"
                ]
                
                # Only include non-empty fields
                text = "\n".join([part for part in text_parts if part.split(': ')[1].strip()])
                
                if text.strip():  # Only add if there's actual content
                    metadata = {
                        "collection": "users",
                        "user_id": user_id,
                        "name": user.get('name', ''),
                        "email": user.get('email', ''),
                        "source": "mongodb"
                    }
                    documents.append(Document(page_content=text, metadata=metadata))
                    user_count += 1
                    print(f"Added user {user_count}: {user.get('name', '')}")
            except Exception as e:
                print(f"Error processing user: {str(e)}")
                continue

        # Process profiles collection
        print("\nProcessing profiles...")
        profile_count = 0
        profiles_collection = db.profiles
        for profile in profiles_collection.find():
            try:
                text_parts = [
                    f"Username: {profile.get('username', '')}",
                    f"Phone: {profile.get('phoneNumber', '')}",
                    f"City: {profile.get('city', '')}",
                    f"Country: {profile.get('country', '')}",
                    f"State: {profile.get('state', '')}",
                    f"Email: {profile.get('email', '')}",
                    f"Address: {profile.get('address', '')}",
                    f"Status: {profile.get('status', '')}",
                    f"Avatar: {profile.get('avatarUrl', '')}"
                ]
                
                # Only include non-empty fields
                text = "\n".join([part for part in text_parts if part.split(': ')[1].strip()])
                
                if text.strip():  # Only add if there's actual content
                    metadata = {
                        "collection": "profiles",
                        "user_id": str(profile.get('userId', '')),
                        "username": profile.get('username', ''),
                        "source": "mongodb"
                    }
                    documents.append(Document(page_content=text, metadata=metadata))
                    profile_count += 1
                    print(f"Added profile {profile_count}: {profile.get('username', '')}")
            except Exception as e:
                print(f"Error processing profile: {str(e)}")
                continue

        print(f"\nTotal documents gathered: {len(documents)}")
        print(f"- Posts: {post_count}")
        print(f"- Users: {user_count}")
        print(f"- Profiles: {profile_count}")
        
        if len(documents) == 0:
            print("No valid documents found in the database. Please add some data first.")
            return None
            
        print("\nSplitting documents into chunks...")
        chunks = splitter.split_documents(documents)
        print(f"Created {len(chunks)} chunks")
        
        if not GEMINI_API_KEY:
            print("❌ GEMINI_API_KEY not found in environment variables!")
            return None
            
        print("\nGenerating embeddings and building vector store...")
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001", 
            google_api_key=GEMINI_API_KEY
        )
        
        vector_db = FAISS.from_documents(chunks, embeddings)
        vector_db.save_local(DB_PATH)
        print("✅ Vector database built and saved successfully!")
        return vector_db
        
    except Exception as e:
        print(f"❌ Error building vector database: {str(e)}")
        return None

def load_vector_db():
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY not found in environment variables!")
        return None
        
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GEMINI_API_KEY)
    
    if os.path.exists(DB_PATH):
        try:
            print("Loading existing vector database...")
            return FAISS.load_local(DB_PATH, embeddings, allow_dangerous_deserialization=True)
        except Exception as e:
            print(f"❌ Error loading vector database: {str(e)}")
            print("Attempting to rebuild...")
            return build_vector_db()
    else:
        print("No existing vector database found. Building new one...")
        return build_vector_db()

if __name__ == "__main__":
    load_vector_db()
