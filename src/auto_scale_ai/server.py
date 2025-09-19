#!/usr/bin/env python3
"""
Simple MCP Server with HTTP transport
Provides a tool to get current server time and returns the bearer token from the request.
"""

from typing import Dict, Any, Optional

class MCPServer:
    def __init__(self):
        self.ticket_id = 42

        self.tools = {
            "generate_ticket": {
                "name": "generate_ticket",
                "description": "Generate a ticket for the customer",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }

    def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": True}
            },
            "serverInfo": {
                "name": "auto-scale-ai",
                "version": "1.0.0"
            }
        }

    def handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request"""
        return {
            "tools": list(self.tools.values())
        }

    ticket_id = 0
    def handle_tools_call(self, params: Dict[str, Any], bearer_token: Optional[str]) -> Dict[str, Any]:
        """Handle tools/call request"""
        tool_name = params.get("name")

        if tool_name == "generate_ticket":
            self.ticket_id += 1
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Ticket generated: ID: {self.ticket_id}"
                    }
                ]
            }
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def handle_request(self, method: str, data: Dict[str, Any], bearer_token: Optional[str]) -> Dict[str, Any]:
        """Route MCP requests to appropriate handlers"""
        if method == "initialize":
            return self.handle_initialize(data.get("params", {}))
        elif method == "tools/list":
            return self.handle_tools_list(data.get("params", {}))
        elif method == "tools/call":
            return self.handle_tools_call(data.get("params", {}), bearer_token)
        else:
            raise ValueError(f"Unknown method: {method}")
