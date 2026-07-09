# LM Studio Context Compression MCP Server

Automatic context compression directly integrated with LM Studio chat via MCP.

## How It Works

The MCP server automatically:
1. **Monitors** conversation token count in real-time
2. **Detects** when approaching token limit (70% by default)
3. **Summarizes** old messages using the model itself
4. **Compresses** context transparently during chat

## Usage via MCP JSON Commands

### 1. Add Message (Auto-compress if needed)

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "add_message",
    "arguments": {
      "role": "user",
      "content": "What is machine learning?"
    }
  },
  "id": 1
}
```

**Response:**
```json
{
  "message_added": true,
  "current_tokens": 150,
  "compression_triggered": false,
  "messages_count": 3
}
```

### 2. Get Current Context

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "get_context",
    "arguments": {}
  },
  "id": 2
}
```

**Response:**
```json
{
  "messages": [
    {"role": "user", "content": "What is ML?"},
    {"role": "assistant", "content": "Machine learning..."}
  ],
  "token_count": 150,
  "context_limit": 4000,
  "compression_threshold": 0.7,
  "needs_compression": false
}
```

### 3. Manually Trigger Compression

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "compress",
    "arguments": {}
  },
  "id": 3
}
```

**Response:**
```json
{
  "status": "compression_complete",
  "old_messages_compressed": 5,
  "new_token_count": 220,
  "summary": "Previous discussion covered ML basics and neural networks..."
}
```

### 4. Get Statistics

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "get_stats",
    "arguments": {}
  },
  "id": 4
}
```

**Response:**
```json
{
  "total_messages": 12,
  "total_tokens": 2800,
  "compression_active": true,
  "timestamp": "2026-07-08T17:00:00.123456"
}
```

### 5. Clear History

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "clear",
    "arguments": {}
  },
  "id": 5
}
```

## Using in Claude Code / Chat

You can call these methods directly in Claude Code:

```python
# Example: Use context compression in your workflow
result = call_mcp_tool("context-compression", "add_message", {
    "role": "user",
    "content": "Analyze this large document..."
})

if result.get("compression_triggered"):
    print("Context was automatically compressed!")

stats = call_mcp_tool("context-compression", "get_stats")
print(f"Current tokens: {stats['total_tokens']}/{stats['context_limit']}")
```

## Configuration

Located in `.roo/mcp.json`:

```json
"context-compression": {
  "type": "stdio",
  "command": "python",
  "args": ["E:/PythonChimera/Chimera/mcp_context_server.py"],
  "alwaysAllow": ["add_message", "get_context", "compress", "clear", "get_stats"]
}
```

## Advanced Configuration

Edit `mcp_context_server.py` to customize:

```python
self.context_limit = 4000          # Max tokens before compression
self.compression_threshold = 0.7   # Compress at 70% of limit
self.model = "qwen3.6-35b..."      # Model for summarization
```

## How Compression Works

1. **Old messages stored** → Waiting for threshold
2. **Token count ≥ 70% of limit** → Compression triggered
3. **Model summarizes** → Old messages condensed to 2-3 sentence summary
4. **Recent kept intact** → Last 3 messages untouched for coherence
5. **Conversation continues** → No interruption to user

## Benefits

✅ **Unlimited conversations** — Never hit token limits
✅ **Seamless** — Works automatically in background
✅ **Preserves context** — Recent messages keep full detail
✅ **Smart summaries** — Model-generated, not rule-based
✅ **Transparent** — User doesn't need to manage it

## Status

- ✅ MCP server registered in `.roo/mcp.json`
- ✅ Available via MCP tools in Claude Code
- ✅ Ready to integrate with LM Studio chat

Start using: Call any of the methods above via MCP tools!
