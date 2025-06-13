import openai
import os
from typing import List, Dict, Optional
import base64
from io import BytesIO
from PIL import Image

class LLMClient:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def generate_answer(self, question: str, context: List[Dict], image_data: Optional[str] = None) -> str:
        """Generate answer using LLM with context"""
        
        # Prepare context text
        context_text = "\n\n".join([
            f"Source: {item['title']}\nURL: {item['url']}\nContent: {item['content'][:1000]}..."
            for item in context[:5]  # Use top 5 most relevant contexts
        ])
        
        system_prompt = """You are a helpful teaching assistant for the Tools in Data Science course at IIT Madras. 
        You have access to course content and discourse forum discussions. 
        
        Answer student questions based on the provided context. Be specific and helpful.
        If you don't know something or the information isn't in the context, say so clearly.
        
        When referencing specific information, mention which source it comes from."""
        
        user_prompt = f"""Question: {question}
        
        Context:
        {context_text}
        
        Please provide a helpful answer based on the context above."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Add image if provided
        if image_data:
            try:
                # Decode base64 image
                image_bytes = base64.b64decode(image_data)
                # Add image to message (for GPT-4 Vision)
                messages[-1]["content"] = [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                ]
            except Exception as e:
                print(f"Error processing image: {e}")
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo" if not image_data else "gpt-4-vision-preview",
                messages=messages,
                max_tokens=1000,
                temperature=0.3
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"I apologize, but I'm unable to process your question right now. Error: {str(e)}"