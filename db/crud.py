from pymongo import MongoClient
from typing import Dict, Any

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")  
db = client["aiSolutions"] 
collection = db["solutions"]  # Collection for AI generated solutions

# ------------------------ # with AI generation
# 1. CREATE (Insert Solution)
# ------------------------
def create_solution(solution_data: Dict[str, Any]) -> str:
    """
    Store a new solution in the database
    
    Args:
        solution_data: Solution data from round_stream
    Returns:
        str: Inserted document ID
    """
    result = collection.insert_one(solution_data)
    return str(result.inserted_id)

# ------------------------ # with AI help
# 2. READ (Query Solutions)
# ------------------------
def get_solution_by_id(solution_id: str) -> Dict[str, Any]:
    """Get a specific solution by its ID"""
    from bson.objectid import ObjectId
    return collection.find_one({"_id": ObjectId(solution_id)})

def get_solutions_by_problem_id(problem_id: str) -> list:
    """Get all solutions for a specific problem ID"""
    return list(collection.find({"id": problem_id}))

# ------------------------ # with AI help
# 3. UPDATE (Modify Solution)
# ------------------------
def update_solution(solution_id: str, updates: Dict[str, Any]) -> bool:
    """
    Update an existing solution
    
    Args:
        solution_id: ID of the solution to update
        updates: Fields to update
    Returns:
        bool: True if update was successful
    """
    from bson.objectid import ObjectId
    result = collection.update_one(
        {"_id": ObjectId(solution_id)},
        {"$set": updates}
    )
    return result.modified_count > 0

# ------------------------ # with AI help
# 4. DELETE (Remove Solution)
# ------------------------
def delete_solution(solution_id: str) -> bool:
    """Delete a solution by its ID"""
    from bson.objectid import ObjectId
    result = collection.delete_one({"_id": ObjectId(solution_id)})
    return result.deleted_count > 0

# ------------------------ # with AI help
# Run CRUD Operations
# ------------------------
if __name__ == "__main__":
    create_solution({"name": "John Doe", "age": 30, "city": "New York"})      # Create
    get_solution_by_id("some_solution_id")       # Read
    update_solution("some_solution_id", {"age": 31})      # Update
    get_solution_by_id("some_solution_id")       # Read Again
    delete_solution("some_solution_id")      # Delete
    get_solution_by_id("some_solution_id")       # Final Read

# Close the connection
client.close()