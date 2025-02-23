from typing import Dict, Any, Optional, AsyncGenerator, List
import asyncio
from agents.breaker import AIBreaker, BreakerRequest
from agents.solver import Solver, SolverRequest, SubProblem
import datetime
from main import get_client
import logging
from mongodb_client import connect_to_mongo, close_mongo_connection
from db.find_history import get_solution_history, save_solution
import uuid

logger = logging.getLogger(__name__)

async def round_stream(
    problem: str,
    client,  # MongoDB客户端实例
    follow_up_question: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    parent_id: Optional[str] = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    处理问题并生成解决方案的流式包装函数
    
    Args:
        problem (str): 原始问题描述
        client: MongoDB客户端实例
        follow_up_question (Optional[str]): 可选的后续问题
        metadata (Optional[Dict[str, Any]]): 额外的元数据
        parent_id (Optional[str]): 父节点ID
    """
    try:
        # 获取历史记录
        solution_history = []
        if parent_id:
            solution_history = await get_solution_history(parent_id, client)
        
        breaker = AIBreaker()
        breaker_request = BreakerRequest(
            originalInput=problem,
            followUpQuestion=follow_up_question,
            metadata={"language": metadata.get('language', 'English')},
            context={"solutionHistory": solution_history}
        )

        breakdown = await breaker.process_request(breaker_request)
        
        solutions = []
        sub_problems = breakdown.get('data', {}).get('subProblems', [])
        
        for sub_problem in sub_problems:
            solver = Solver(language=breakdown.get('metadata', {}).get('language', metadata.get('language', 'English')))
            solver_request = SolverRequest(
                subProblem=SubProblem(
                    title=sub_problem.get('title', ''),
                    description=sub_problem.get('description', ''),
                    objective=sub_problem.get('objective', ''),
                    id=sub_problem.get('id', ''),
                    language=breakdown.get('metadata', {}).get('language', metadata.get('language', 'English'))
                ),
                metadata=breakdown.get('metadata', {'language': metadata.get('language', 
                                                                         'English')}),
                context={"solutionHistory": solution_history}
            )
            solution = await solver.solve(solver_request)
            
            # 准备解决方案文档
            current_solution = {
                'title': sub_problem.get('title'),
                'description': sub_problem.get('description'),
                'objective': sub_problem.get('objective'),
                'solution': solution.content,
                'problem': problem,
                'follow_up_question': follow_up_question,
                'created_at': datetime.datetime.utcnow(),
                'parent_id': parent_id,
                'metadata': metadata,
                '_id': str(uuid.uuid4()),
                'priority': 0
            }
            
            # 保存到数据库并获取正确的ID
            saved_id = await save_solution(current_solution, client)
            if saved_id:
                current_solution['id'] = str(saved_id)
                # 返回事件
                yield {
                    "event": "solver_output",
                    "data": current_solution
                }
            
    except Exception as e:
        logger.error(f"Error in round stream: {str(e)}")
        raise

if __name__ == "__main__":
    async def main():
        client = None
        try:
            # 设置日志级别
            logging.basicConfig(level=logging.INFO)
            
            # 初始化数据库连接
            await connect_to_mongo()
            client = get_client()
            
            # 验证数据库连接
            db = client['nodetree']
            collections = await db.list_collection_names()
            print(f"Available collections: {collections}")
            
            # 第一次调用 - 创建初始节点
            print("\n=== 创建初始节点：基础待办事项应用 ===")
            first_id = None
            async for event in round_stream(
                problem="创建一个简单的待办事项应用",
                client=client,
                metadata={"language": "Chinese"}
            ):
                print(f"\n事件类型: {event['event']}")
                print("数据:", event['data'])
                print("-" * 80)
                first_id = event['data']['id']

            # 第二次调用 - 添加用户认证
            print("\n=== 添加用户认证功能 ===")
            second_id = None
            async for event in round_stream(
                problem="如何添加用户认证功能？",
                client=client,
                follow_up_question="需要使用什么技术栈？",
                metadata={"language": "Chinese"},
                parent_id=first_id
            ):
                print(f"\n事件类型: {event['event']}")
                print("数据:", event['data'])
                print("-" * 80)
                second_id = event['data']['id']

            # 第三次调用 - 添加任务分类功能
            print("\n=== 添加任务分类功能 ===")
            third_id = None
            async for event in round_stream(
                problem="如何实现任务分类功能？",
                client=client,
                follow_up_question="如何设计数据库模型？",
                metadata={"language": "Chinese"},
                parent_id=second_id
            ):
                print(f"\n事件类型: {event['event']}")
                print("数据:", event['data'])
                print("-" * 80)
                third_id = event['data']['id']

            # 第四次调用 - 添加任务优先级
            print("\n=== 添加任务优先级功能 ===")
            async for event in round_stream(
                problem="如何添加任务优先级功能？",
                client=client,
                follow_up_question="如何在界面上展示不同优先级？",
                metadata={"language": "Chinese"},
                parent_id=third_id
            ):
                print(f"\nevent: {event['event']}")
                print("data:", event['data'])
                print("-" * 80)


            print("\n=== 显示完整解决方案历史记录链 ===")
            history = await get_solution_history(third_id, client)
            print("\n完整历史数据结构:")
            for idx, item in enumerate(history, 1):
                print(f"\n解决方案 #{idx}:")
                print("数据结构:")
                print({
                    "id": item.get('id'),
                    "title": item.get('title'),
                    "description": item.get('description'),
                    "objective": item.get('objective'),
                    "solution": item.get('solution'),
                    "problem": item.get('problem'),
                    "follow_up_question": item.get('follow_up_question'),
                    "created_at": item.get('created_at'),
                    "parent_id": item.get('parent_id'),
                    "metadata": item.get('metadata')
                })
                print("-" * 80)
            print("history:")
            print(history)
            # 显示历史记录的层级关系
            print("\n解决方案层级结构:")
            def print_tree(items, parent_id=None, level=0):
                for item in items:
                    if item.get('parent_id') == parent_id:
                        print("  " * level + f"├── {item.get('title')} (ID: {item.get('id')})")
                        print_tree(items, item.get('id'), level + 1)
            
            print_tree(history)

        except Exception as e:
            print(f"发生错误: {e}")
            raise
        finally:
            if client:
                await close_mongo_connection()

    asyncio.run(main())
