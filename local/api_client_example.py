#!/usr/bin/env python3
"""
EY Data Integration - API Client Example
Shows how to interact with the main Gemini Orchestration Agent via API
"""
import requests
import json
from typing import Dict, Any


class EYDataIntegrationClient:
    """
    Client for the EY Data Integration AI Assistant
    
    Main endpoint: POST http://localhost:8002/chat
    """
    
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
        self.session_id = None
    
    def chat(self, message: str, session_id: str = None) -> Dict[str, Any]:
        """
        Send a message to the AI assistant
        
        Args:
            message: Natural language message
            session_id: Optional session ID for conversation continuity
        
        Returns:
            Response dictionary with:
                - answer: AI response text
                - confidence: Confidence score (0-100)
                - reasoning: Explanation of actions taken
        """
        url = f"{self.base_url}/chat"
        
        payload = {
            "message": message,
            "session_id": session_id or self.session_id or "default"
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def merge_datasets(self, table1: str, table2: str) -> Dict[str, Any]:
        """Merge two datasets"""
        return self.chat(f"merge {table1} and {table2}")
    
    def analyze_table(self, table_name: str) -> Dict[str, Any]:
        """Analyze a table schema"""
        return self.chat(f"analyze {table_name}")
    
    def validate_quality(self, table_name: str) -> Dict[str, Any]:
        """Validate data quality"""
        return self.chat(f"validate data quality in {table_name}")


# Example Usage
if __name__ == "__main__":
    # Initialize client
    client = EYDataIntegrationClient()
    
    print("="*80)
    print("EY DATA INTEGRATION - API CLIENT EXAMPLE")
    print("="*80)
    
    # Example 1: Simple greeting
    print("\n📝 Example 1: Simple greeting")
    response = client.chat("hello")
    print(f"Response: {response['answer'][:100]}...")
    
    # Example 2: Merge two datasets
    print("\n📝 Example 2: Merge datasets")
    response = client.merge_datasets(
        "RAW_ULTIMATE_MERGE_001_ACCOUNTS_DATASET_1",
        "RAW_ULTIMATE_MERGE_001_ACCOUNTS_DATASET_2"
    )
    print(f"Response: {response['answer']}")
    print(f"Confidence: {response['confidence']}%")
    
    # Example 3: Analyze a table
    print("\n📝 Example 3: Analyze table")
    response = client.analyze_table("UNIFIED_ACCOUNTS")
    print(f"Response: {response['answer'][:200]}...")
    
    # Example 4: Custom query
    print("\n📝 Example 4: Custom natural language query")
    response = client.chat("What tables are available in Snowflake?")
    print(f"Response: {response['answer'][:200]}...")
    
    print("\n" + "="*80)
    print("✅ API Client examples complete!")
    print("="*80)
