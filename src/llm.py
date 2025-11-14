import os
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()


class LLM:
    """
    A class to interact with OpenAI API for processing prompts and returning responses.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-5-nano"):
        """
        Initialize the LLM class with OpenAI API configuration.
        
        Args:
            api_key: OpenAI API key. If not provided, will try to get from OPENAI_API_KEY 
                    environment variable or .env file.
            model: The model to use (default: "gpt-5-nano")
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. Provide it as an argument, set OPENAI_API_KEY "
                "environment variable, or add OPENAI_API_KEY to your .env file."
            )
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
    
    def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate a response from the LLM based on the provided prompt.
        
        Args:
            prompt: The user prompt/request
            system_prompt: Optional system prompt to set the behavior of the assistant
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional parameters to pass to the OpenAI API
        
        Returns:
            The generated response as a string
        """
        # Combine system prompt and user prompt if system prompt is provided
        input_text = prompt
        if system_prompt:
            input_text = f"{system_prompt}\n\n{prompt}"
        
        # Build request parameters
        request_params = {
            "model": self.model,
            "input": input_text,
            **kwargs
        }
        
        # Add optional parameters if provided
        if max_tokens is not None:
            request_params["max_tokens"] = max_tokens
        
        try:
            response = self.client.responses.create(**request_params)
            return response.output_text.strip()
        
        except Exception as e:
            raise Exception(f"Error generating response from OpenAI API: {str(e)}")
    
    def update_model(self, model: str):
        """Update the default model to use."""
        self.model = model


# Test the LLM class
if __name__ == "__main__":
    import sys
    
    print("="*80)
    print("LLM CLASS TEST")
    print("="*80)
    
    try:
        # Test 1: Initialize LLM
        print("\n1. Initializing LLM...")
        llm = LLM()
        print(f"   ✓ LLM initialized")
        print(f"   Model: {llm.model}")
        
        # Test 2: Simple prompt
        print("\n2. Testing simple prompt...")
        test_prompt = "Write a one-sentence summary about artificial intelligence."
        print(f"   Prompt: {test_prompt}")
        response = llm.generate_response(test_prompt)
        print(f"   ✓ Response received ({len(response)} characters)")
        print(f"   Response: {response[:200]}..." if len(response) > 200 else f"   Response: {response}")
        
        # Test 3: Prompt with system message
        print("\n3. Testing prompt with system message...")
        system_prompt = "You are a helpful assistant that provides concise answers."
        user_prompt = "What is machine learning?"
        print(f"   System: {system_prompt}")
        print(f"   User: {user_prompt}")
        response = llm.generate_response(user_prompt, system_prompt=system_prompt)
        print(f"   ✓ Response received ({len(response)} characters)")
        print(f"   Response: {response[:200]}..." if len(response) > 200 else f"   Response: {response}")
        
        # Test 4: Another simple prompt
        print("\n4. Testing another prompt...")
        response = llm.generate_response("Tell me a fun fact about space.")
        print(f"   ✓ Response received")
        print(f"   Response: {response[:200]}..." if len(response) > 200 else f"   Response: {response}")
        
        print("\n" + "="*80)
        print("ALL TESTS PASSED ✓")
        print("="*80)
        
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease ensure you have:")
        print("  1. Created a .env file in the project root")
        print("  2. Added OPENAI_API_KEY=your-api-key-here to the .env file")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
