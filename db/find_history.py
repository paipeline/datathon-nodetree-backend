from typing import Dict, Any, List, Optional
from bson import ObjectId
import uuid
import logging
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

async def get_solution_history(parent_id: str, client: AsyncIOMotorClient) -> List[Dict[str, Any]]:
    """
    递归获取解决方案历史记录
    
    Args:
        parent_id (str): 父节点id
        client (AsyncIOMotorClient): MongoDB客户端实例
    
    Returns:
        List[Dict[str, Any]]: 历史记录列表
    """
    history = []
    current_id = parent_id
    
    while current_id is not None:
        try:
            # 如果是UUID格式，转换为ObjectId格式
            if len(current_id) == 36:  # UUID格式的长度
                hex_id = uuid.UUID(current_id).hex[:24]
                current_id = hex_id
            
            # 使用传入的client实例
            db = client['nodetree']
            collection = db['nodes']
            solution = await collection.find_one({"_id": ObjectId(current_id)})
            
            if solution:
                # 确保返回的解决方案包含正确格式的id字段
                if '_id' in solution:
                    # 将ObjectId转换回UUID格式
                    solution['id'] = current_id if len(current_id) == 36 else str(solution['_id'])
                history.append(solution)
                current_id = solution.get('parent_id')
                
                # 如果parent_id是ObjectId格式，转换为UUID格式
                if current_id and not len(current_id) == 36:
                    try:
                        # 将ObjectId扩展为UUID格式
                        current_id = str(uuid.UUID(current_id + '0' * 12))
                    except ValueError:
                        logger.error(f"Error converting ObjectId to UUID: {current_id}")
                        break
            else:
                break
        except Exception as e:
            logger.error(f"Error getting solution history: {str(e)}")
            break
    
    return list(reversed(history))

async def save_solution(solution_data: Dict[str, Any], client: AsyncIOMotorClient) -> Optional[str]:
    """
    保存解决方案到数据库
    
    Args:
        solution_data (Dict[str, Any]): 解决方案数据
        client (AsyncIOMotorClient): MongoDB客户端实例
    
    Returns:
        Optional[str]: 成功时返回解决方案ID，失败时返回None
    """
    try:
        # 生成新的UUID如果没有的话
        if 'id' not in solution_data:
            solution_data['id'] = str(uuid.uuid4())
        
        # 转换UUID为MongoDB的ObjectId
        hex_id = uuid.UUID(solution_data['id']).hex[:24]
        solution_data['_id'] = ObjectId(hex_id)
        
        # 获取MongoDB集合
        db = client['nodetree']
        collection = db['nodes']
        
        logger.info(f"Attempting to save solution with ID: {solution_data['id']}")
        
        # 保存到数据库
        result = await collection.replace_one(
            {'_id': solution_data['_id']},
            solution_data,
            upsert=True
        )
        
        logger.info(f"Save result acknowledged: {result.acknowledged}")
        if result.acknowledged:
            logger.info(f"Modified count: {result.modified_count}, Upserted ID: {result.upserted_id}")
            
            # 验证保存是否成功
            saved_solution = await collection.find_one({'_id': solution_data['_id']})
            if saved_solution:
                logger.info(f"Successfully verified solution save with ID: {solution_data['id']}")
                return solution_data['id']
            
        logger.error("Solution was not saved successfully")
        return None
        
    except Exception as e:
        logger.error(f"Error saving solution to database: {str(e)}")
        return None
