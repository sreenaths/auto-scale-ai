from locust import HttpUser, task, between
import json

class WebUser(HttpUser):
    wait_time = between(0.05, 0.2)

    def on_start(self):
        """Set up headers and common data for requests"""
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer test-token-123"
        }

    @task(10)
    def agent_initialize(self):
        """Test the agent endpoint with initialize request"""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "locust-test",
                    "version": "1.0.0"
                }
            }
        }
        self.client.post("/agent", json=payload, headers=self.headers)

    @task(15)
    def agent_tools_list(self):
        """Test the agent endpoint with tools/list request"""
        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        self.client.post("/agent", json=payload, headers=self.headers)

    @task(20)
    def agent_tools_call(self):
        """Test the agent endpoint with tools/call request"""
        payload = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "generate_ticket"
            }
        }
        self.client.post("/agent", json=payload, headers=self.headers)

    @task(1)
    def health(self):
        """Test the health endpoint"""
        self.client.get("/health")
