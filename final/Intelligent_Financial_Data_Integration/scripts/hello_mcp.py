#!/usr/bin/env python3
"""
MCP Server with Gemini API Integration
This script provides a Model Context Protocol (MCP) server that integrates with Google's Gemini API
to provide intelligent chatbot responses.
"""

import json
import sys
import os
import asyncio
import logging
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiMCPServer:
    def __init__(self):
        """Initialize the MCP server with Gemini API configuration."""
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        # Configure Gemini API
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Safety settings for content filtering
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
        
        logger.info("Gemini MCP Server initialized successfully")

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming MCP requests and generate responses using Gemini."""
        try:
            method = request.get('method')
            params = request.get('params', {})
            
            if method == 'chatbot/query':
                return await self.handle_chatbot_query(params)
            elif method == 'chatbot/health':
                return await self.handle_health_check()
            else:
                return {
                    'error': {
                        'code': -32601,
                        'message': f'Method not found: {method}'
                    }
                }
                
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return {
                'error': {
                    'code': -32603,
                    'message': f'Internal error: {str(e)}'
                }
            }

    async def handle_chatbot_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle chatbot queries using Gemini API."""
        try:
            user_message = params.get('message', '')
            context = params.get('context', {})
            conversation_history = params.get('history', [])
            
            if not user_message:
                return {
                    'error': {
                        'code': -32602,
                        'message': 'Message parameter is required'
                    }
                }
            
            # Build context-aware prompt
            prompt = self.build_contextual_prompt(user_message, context, conversation_history)
            
            # Generate response using Gemini
            response = await self.generate_gemini_response(prompt)
            
            return {
                'result': {
                    'response': response,
                    'timestamp': self.get_timestamp(),
                    'model': 'gemini-pro',
                    'context': context
                }
            }
            
        except Exception as e:
            logger.error(f"Error in chatbot query: {str(e)}")
            return {
                'error': {
                    'code': -32603,
                    'message': f'Failed to generate response: {str(e)}'
                }
            }

    def build_contextual_prompt(self, message: str, context: Dict[str, Any], history: List[Dict[str, str]]) -> str:
        """Build a context-aware prompt for Gemini."""
        prompt_parts = [
            "You are an intelligent AI assistant for a Financial Data Integration platform.",
            "You help users with data integration, mapping, analysis, and technical questions.",
            "Provide helpful, accurate, and professional responses.",
            ""
        ]
        
        # Add context information
        if context:
            prompt_parts.append("Current context:")
            for key, value in context.items():
                prompt_parts.append(f"- {key}: {value}")
            prompt_parts.append("")
        
        # Add conversation history
        if history:
            prompt_parts.append("Recent conversation:")
            for entry in history[-5:]:  # Last 5 exchanges
                role = entry.get('role', 'user')
                content = entry.get('content', '')
                prompt_parts.append(f"{role}: {content}")
            prompt_parts.append("")
        
        # Add current message
        prompt_parts.append(f"User: {message}")
        prompt_parts.append("Assistant:")
        
        return "\n".join(prompt_parts)

    async def generate_gemini_response(self, prompt: str) -> str:
        """Generate response using Gemini API."""
        try:
            # Configure generation parameters
            generation_config = {
                'temperature': 0.7,
                'top_p': 0.8,
                'top_k': 40,
                'max_output_tokens': 1024,
            }
            
            # Generate response
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=self.safety_settings
            )
            
            if response.text:
                return response.text.strip()
            else:
                return "I apologize, but I couldn't generate a response at this time. Please try again."
                
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            return f"I'm experiencing technical difficulties. Error: {str(e)}"

    async def handle_health_check(self) -> Dict[str, Any]:
        """Handle health check requests."""
        try:
            # Test Gemini API connectivity
            test_response = self.model.generate_content("Hello")
            return {
                'result': {
                    'status': 'healthy',
                    'gemini_connected': bool(test_response.text),
                    'timestamp': self.get_timestamp()
                }
            }
        except Exception as e:
            return {
                'error': {
                    'code': -32603,
                    'message': f'Health check failed: {str(e)}'
                }
            }

    def get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'

    async def run_stdio_server(self):
        """Run the MCP server using stdio transport."""
        logger.info("Starting MCP server with stdio transport")
        
        while True:
            try:
                # Read request from stdin
                line = sys.stdin.readline()
                if not line:
                    break
                
                # Parse JSON request
                request = json.loads(line.strip())
                
                # Process request
                response = await self.process_request(request)
                
                # Send response to stdout
                print(json.dumps(response))
                sys.stdout.flush()
                
            except json.JSONDecodeError as e:
                error_response = {
                    'error': {
                        'code': -32700,
                        'message': f'Parse error: {str(e)}'
                    }
                }
                print(json.dumps(error_response))
                sys.stdout.flush()
                
            except Exception as e:
                logger.error(f"Server error: {str(e)}")
                error_response = {
                    'error': {
                        'code': -32603,
                        'message': f'Internal server error: {str(e)}'
                    }
                }
                print(json.dumps(error_response))
                sys.stdout.flush()

def main():
    """Main entry point for the MCP server."""
    try:
        server = GeminiMCPServer()
        asyncio.run(server.run_stdio_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed to start: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()


