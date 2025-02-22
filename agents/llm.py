from typing import Optional, List, Dict, Any
from litellm import completion

class LiteLLMWrapper:
    def __init__(self, model: str = "gpt-3.5-turbo", temperature: float = 0.7):
        """
        初始化 LiteLLM 封装类
        
        Args:
            model: 要使用的模型名称
            temperature: 生成温度参数
        """
        self.model = model
        self.temperature = temperature

    async def generate(
        self, 
        prompt: str,
        system_message: Optional[str] = None,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
    ) -> str:
        """
        生成文本响应
        
        Args:
            prompt: 用户输入提示
            system_message: 系统消息
            max_tokens: 最大生成token数
            stop: 停止生成的标记列表
        
        Returns:
            生成的文本响应
        """
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        response = await completion(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=max_tokens,
            stop=stop
        )

        return response.choices[0].message.content

    async def generate_with_history(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
    ) -> str:
        """
        基于对话历史生成响应
        
        Args:
            messages: 对话历史消息列表
            max_tokens: 最大生成token数
            stop: 停止生成的标记列表
            
        Returns:
            生成的文本响应
        """
        response = await completion(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=max_tokens,
            stop=stop
        )

        return response.choices[0].message.content
