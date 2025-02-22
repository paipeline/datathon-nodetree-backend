from typing import Optional, List, Dict, Any
from litellm import completion
import logging
from dotenv import load_dotenv

load_dotenv()

class LiteLLMWrapper:
    def __init__(
        self, 
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
    ):
        """
        Initialize the LLM wrapper
        
        Args:
            model: LLM model name
            temperature: Generation temperature (higher = more random, lower = more deterministic)
        """
        self.model = model
        self.temperature = temperature
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
        json_mode: bool = False,
    ) -> str:
        """
        Generate a response with error handling
        
        Args:
            prompt: Input prompt for generation
            system_message: Optional system message
            max_tokens: Maximum number of tokens to generate
            stop: List of stop sequences
            json_mode: Whether to force JSON format response
            
        Returns:
            Generated text content
        """
        try:
            # Prepare message list
            messages = self._prepare_messages(prompt, system_message, json_mode)
            
            # Call LLM to generate response
            response = completion(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=max_tokens,
                stop=stop,
                response_format={"type": "json_object"} if json_mode else None
            )
            
            self._log_response(response)
            return response.choices[0].message.content

        except Exception as e:
            self._handle_error(e, prompt)
            raise

    def _prepare_messages(self, prompt: str, system_message: Optional[str], json_mode: bool) -> List[Dict[str, str]]:
        """Prepare the message list to send to the LLM"""
        messages = []
        if json_mode:
            system_msg = self._get_json_system_message(system_message)
            messages.append({"role": "system", "content": system_msg})
            prompt = f"Please provide the response to the following in JSON format: {prompt}"
        elif system_message:
            messages.append({"role": "system", "content": system_message})
        
        messages.append({"role": "user", "content": prompt})
        return messages

    def _get_json_system_message(self, system_message: Optional[str]) -> str:
        """Get system message for JSON mode"""
        default_msg = "You are a helpful assistant. Please provide your response in JSON format."
        return (system_message + " Respond in JSON format.") if system_message else default_msg

    def _log_response(self, response: Any) -> None:
        """Log the generated response"""
        self.logger.info("Generation successful")
        self.logger.debug(f"Response: {response.choices[0].message.content[:100]}...")

    def _handle_error(self, error: Exception, prompt: str) -> None:
        """Handle errors and log them"""
        self.logger.error(f"Generation failed: {str(error)}")
        self.logger.debug(f"Failed prompt: {prompt}")

    async def generate_with_history(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
        json_mode: bool = False,
    ) -> str:
        """
        Generates a response based on conversation history
        
        Args:
            messages: List of conversation messages
            max_tokens: Maximum number of tokens to generate
            stop: Optional list of stop sequences
            json_mode: If True, forces the response to be in JSON format
        """
        try:
            if json_mode:
                # 在历史消息开头添加系统消息要求 JSON 格式
                messages = [{"role": "system", "content": "Please provide all responses in JSON format."}] + messages
            
            response = await completion(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=max_tokens,
                stop=stop,
                response_format={"type": "json_object"} if json_mode else None
            )
            
            return response.choices[0].message.content

        except Exception as e:
            self.logger.error(f"Generation failed: {str(e)}")
            raise



class RAGLiteLLMWrapper:
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.7):
        self.model = model
        self.temperature = temperature

    async def generate_with_rag(self, prompt: str, max_tokens: Optional[int] = None, stop: Optional[List[str]] = None) -> Dict[str, Any]:
        #TODO
        pass
    async def generate_with_rag_and_history(self, messages: List[Dict[str, str]], max_tokens: Optional[int] = None, stop: Optional[List[str]] = None) -> Dict[str, Any]:
        #TODO
        pass
        


# test
if __name__ == "__main__":
    llm = LiteLLMWrapper()
    response = llm.generate("Hello, world!", json_mode=True)
    print(response)
