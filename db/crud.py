from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")  
db = client["myDatabase"] 
collection = db["myCollection"]  # Collection Name

# ------------------------
# 1. CREATE (Insert Data)
# ------------------------
def create_document():
    document = {"name": "John Doe", "age": 30, "city": "New York"}
    result = collection.insert_one(document)
    print("Inserted Document ID:", result.inserted_id)

# ------------------------
# 2. READ (Query Data)
# ------------------------
def read_documents():
    # Find one document
    user = collection.find_one({"name": "John Doe"})
    print("Found User:", user)

    # Find multiple documents
    users = collection.find({"age": {"$gt": 25}})
    print("Users older than 25:")
    for user in users:
        print(user)

# ------------------------
# 3. UPDATE (Modify Data)
# ------------------------
def update_document():
    result = collection.update_one(
        {"name": "John Doe"},  # Filter
        {"$set": {"age": 31}}   # Update
    )
    print("Matched:", result.matched_count, "Modified:", result.modified_count)

# ------------------------
# 4. DELETE (Remove Data)
# ------------------------
def delete_document():
    result = collection.delete_one({"name": "John Doe"})
    print("Deleted Count:", result.deleted_count)

# ------------------------
# Run CRUD Operations
# ------------------------
if __name__ == "__main__":
    create_document()      # Create
    read_documents()       # Read
    update_document()      # Update
    read_documents()       # Read Again
    delete_document()      # Delete
    read_documents()       # Final Read

# Close the connection
client.close()