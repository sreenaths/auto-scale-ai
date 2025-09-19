# Stateless, short-lived MCP connections

A minimal, stateless, and lightweight way to build remote MCP servers.


### Set Envs
```
export AZURE_OPENAI_ENDPOINT='https://xx-ai-xxxx.openai.azure.com'
export AZURE_OPENAI_MODEL='gpt-4o-xx'
export AZURE_OPENAI_KEY='xxxxxxxxxxxxxxx'
export MCP_BEARER_TOKEN="123xxx456"
```

### Running
Both must be run in two separate tabs
```
uv run uvicorn src.auto_scale_ai.main:app
uv run src/auto_scale_ai/client.py
```
