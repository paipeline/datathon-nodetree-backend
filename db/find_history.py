from typing import Dict, Any, List, Optional
from bson import ObjectId
import uuid
import logging
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

async def get_solution_history(parent_id: str, client: AsyncIOMotorClient) -> List[Dict[str, Any]]:
    """
   
    
    Args:
        parent_id (str):
        client (AsyncIOMotorClient): 
    
    Returns:
        List[Dict[str, Any]]: 
    """
    history = []
    current_id = parent_id
    
    while current_id is not None:
        try:
            if len(current_id) == 36:
                hex_id = uuid.UUID(current_id).hex[:24]
                current_id = hex_id
            db = client['nodetree']
            collection = db['nodes']
            solution = await collection.find_one({"_id": ObjectId(current_id)})
            
            if solution:

                if '_id' in solution:
                    solution['id'] = current_id if len(current_id) == 36 else str(solution['_id'])
                history.append(solution)
                current_id = solution.get('parent_id')
               #with AI generated exception 

                if current_id and not len(current_id) == 36:
                    try:
                      
                        current_id = str(uuid.UUID(current_id + '0' * 12))
                    except ValueError:
                        logger.error(f"Error converting ObjectId to UUID: {current_id}")
                        break
            else:
                break
        except Exception as e:
            logger.error(f"Error getting solution history: {str(e)}")
            break
    

    sorted_history = sorted(
        history,
        key=lambda x: (x.get('priority', 0), -history.index(x)),
        reverse=True
    )
    
    return sorted_history

async def save_solution(solution_data: Dict[str, Any], client: AsyncIOMotorClient) -> Optional[str]:

    try:
        if 'id' not in solution_data:
            solution_data['id'] = str(uuid.uuid4())
        
        hex_id = uuid.UUID(solution_data['id']).hex[:24]
        solution_data['_id'] = ObjectId(hex_id)
    
        db = client['nodetree']
        collection = db['nodes']
        
        logger.info(f"Attempting to save solution with ID: {solution_data['id']}")
        

        result = await collection.replace_one(
            {'_id': solution_data['_id']},
            solution_data,
            upsert=True
        )
        
        logger.info(f"Save result acknowledged: {result.acknowledged}")
        if result.acknowledged:
            logger.info(f"Modified count: {result.modified_count}, Upserted ID: {result.upserted_id}")
            
            saved_solution = await collection.find_one({'_id': solution_data['_id']})
            if saved_solution:
                logger.info(f"Successfully verified solution save with ID: {solution_data['id']}")
                return solution_data['id']
            
        logger.error("Solution was not saved successfully")
        return None
        
    except Exception as e:
        logger.error(f"Error saving solution to database: {str(e)}")
        return None
