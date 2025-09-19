#!/usr/bin/env python3
"""
MCP Client with Azure OpenAI Integration
Connects to the MCP server and uses Azure OpenAI to have conversations with access to server tools.
"""

import json
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from openai import AsyncAzureOpenAI
import os
from datetime import datetime

class MCPClient:
    def __init__(self, server_url: str, bearer_token: Optional[str] = None):
        self.server_url = server_url
        self.bearer_token = bearer_token
        self.session = None
        self.tools = []
        self.initialized = False
        self.request_id = 0

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers including bearer token if provided"""
        headers = {"Content-Type": "application/json"}
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"
        return headers

    def _get_next_id(self) -> int:
        """Get next request ID"""
        self.request_id += 1
        return self.request_id

    async def _send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send JSON-RPC request to MCP server"""
        if params is None:
            params = {}

        request_data = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": method,
            "params": params
        }

        async with self.session.post(
            self.server_url + "/agent",
            json=request_data,
            headers=self._get_headers()
        ) as response:
            result = await response.json()

            if "error" in result:
                raise Exception(f"MCP Error: {result['error']}")

            return result.get("result", {})

    async def initialize(self):
        """Initialize connection with MCP server"""
        if self.initialized:
            return

        result = await self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {}
        })

        print(f"Connected to MCP server: {result.get('serverInfo', {}).get('name', 'Unknown')}")

        # Get available tools
        tools_result = await self._send_request("tools/list")
        self.tools = tools_result.get("tools", [])

        print(f"Available tools: {[tool['name'] for tool in self.tools]}")
        self.initialized = True

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> str:
        """Call a tool on the MCP server"""
        if arguments is None:
            arguments = {}

        result = await self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })

        # Extract text content from the result
        content = result.get("content", [])
        if content and len(content) > 0:
            return content[0].get("text", "No text content returned")

        return "No content returned"

    def get_tools_for_openai(self) -> List[Dict[str, Any]]:
        """Convert MCP tools to OpenAI function format"""
        openai_tools = []

        for tool in self.tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool.get("inputSchema", {
                        "type": "object",
                        "properties": {},
                        "required": []
                    })
                }
            }
            openai_tools.append(openai_tool)

        return openai_tools

class AzureOpenAIClient:
    def __init__(self, endpoint: str, api_key: str, api_version: str = "2024-02-15-preview"):
        self.client = AsyncAzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version
        )

    async def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        model: str = "gpt-4"
    ) -> Dict[str, Any]:
        """Send chat completion request with tools"""
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        return response

class MCPAzureChat:
    def __init__(self, mcp_client: MCPClient, azure_client: AzureOpenAIClient, model: str = "gpt-4"):
        self.mcp_client = mcp_client
        self.azure_client = azure_client
        self.model = model
        self.conversation_history = [{
            "role": "system",
            "content": """You are an AI customer support chat bot working for Orange, an electric vehicle company. You are friendly and helpful. You have access to tools that can help you answer customer questions.
Orange's latest OTA update is crashing, and the cars are not starting! They have an app from which customers can contact you.
Start by assuring the customer that you are aware of the issue and that the engineering team is working on a fix.
You can also provide information about the issue and the following workaround:
1. Try holding the power button for 10 seconds for a soft reset
2. If that doesn't work, do a hard reset by holding the horn and brake for 50 seconds

You can also use the generate_ticket tool to generate a ticket for the customer, if the workarounds don't work.
""",
        }]

    async def chat(self, user_message: str) -> str:
        """Have a conversation with Azure OpenAI using MCP tools"""
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_message})

        # Get tools in OpenAI format
        tools = self.mcp_client.get_tools_for_openai()

        # Send to Azure OpenAI
        response = await self.azure_client.chat_with_tools(
            messages=self.conversation_history,
            tools=tools,
            model=self.model
        )

        message = response.choices[0].message

        # Check if the assistant wants to call a tool
        if message.tool_calls:
            # Add assistant message with tool calls to history
            self.conversation_history.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in message.tool_calls
                ]
            })

            # Execute tool calls
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}

                print(f"Calling tool: {function_name} with args: {function_args}")

                # Call the MCP tool
                tool_result = await self.mcp_client.call_tool(function_name, function_args)

                # Add tool result to conversation history
                self.conversation_history.append({
                    "role": "tool",
                    "content": tool_result,
                    "tool_call_id": tool_call.id
                })

            # Get final response from Azure OpenAI
            final_response = await self.azure_client.chat_with_tools(
                messages=self.conversation_history,
                tools=tools,
                model=self.model
            )

            final_message = final_response.choices[0].message
            self.conversation_history.append({
                "role": "assistant",
                "content": final_message.content
            })

            return final_message.content
        else:
            # No tool calls, just return the response
            self.conversation_history.append({
                "role": "assistant",
                "content": message.content
            })
            return message.content

async def main():
    """Main function to run the MCP + Azure OpenAI client"""

    # Configuration - set these environment variables or modify directly
    MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
    MCP_BEARER_TOKEN = os.getenv("MCP_BEARER_TOKEN", "my-secret-token-123")

    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
    AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_MODEL", "gpt-4")

    if not AZURE_OPENAI_ENDPOINT or not AZURE_OPENAI_KEY:
        print("Error: Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY environment variables")
        print("Example:")
        print("export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com'")
        print("export AZURE_OPENAI_KEY='your-api-key'")
        return

    print("MCP + Azure OpenAI Client")
    print("=" * 40)
    print(f"MCP Server: {MCP_SERVER_URL}")
    print(f"Azure OpenAI Model: {AZURE_OPENAI_MODEL}")
    print()

    try:
        # Initialize clients
        async with MCPClient(MCP_SERVER_URL, MCP_BEARER_TOKEN) as mcp_client:
            azure_client = AzureOpenAIClient(AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY)
            chat = MCPAzureChat(mcp_client, azure_client, AZURE_OPENAI_MODEL)

            print("Chat initialized! Type 'quit' to exit.")
            print("Try asking: 'What did the server return?'")
            print()

            while True:
                try:
                    print("-" * 40)
                    user_input = input("You: ").strip()

                    if user_input.lower() in ['quit', 'exit', 'q']:
                        break

                    if not user_input:
                        continue

                    print("Assistant: ", end="", flush=True)
                    response = await chat.chat(user_input)
                    print(response)
                    print()

                except KeyboardInterrupt:
                    print("\nGoodbye!")
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    print()

    except Exception as e:
        print(f"Failed to initialize: {e}")

if __name__ == "__main__":
    # Required dependencies
    print()

    asyncio.run(main())
