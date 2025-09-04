# MCP Server Configuration Feature

This feature allows users to configure their own Model Context Protocol (MCP) servers in addition to the default AWS documentation server.

## Overview

Each user can now:

- Add custom MCP servers with their own configurations
- Store server configurations securely in S3 with user-specific prefixes
- Use predefined templates for common MCP servers
- Switch between using default AWS documentation and their custom servers

## Architecture

### Backend Changes

1. **Enhanced MCPClientManager** (`backend/agent/mcp_client_manager.py`)

   - Now supports user-specific MCP clients
   - Stores configurations in S3 with prefix `mcp-configs/user_{user_id}/config.json`
   - Falls back to default AWS documentation server if no user config exists

2. **New API Endpoints** (`backend/agent/agent.py`)

   - `GET /mcp-configs/{user_id}` - Get user's MCP server configurations
   - `POST /mcp-configs/{user_id}` - Save user's MCP server configurations
   - `DELETE /mcp-configs/{user_id}` - Delete user's MCP server configurations
   - `GET /mcp-templates` - Get predefined MCP server templates
   - Updated `GET /tools?user_id={user_id}` - Get tools for specific user

3. **Updated Chat Endpoint**
   - Now uses user-specific MCP client when available
   - Falls back to default AWS documentation if no user config

### Frontend Changes

1. **New Component** (`frontend/app/components/MCPConfigButton.tsx`)

   - Modal interface for managing MCP server configurations
   - Template selection for common servers
   - Form validation and environment variable management

2. **Updated Main Interface** (`frontend/app/(chat)/page.tsx`)

   - Added MCP configuration button to the toolbar
   - Passes user ID to tools hook for user-specific tool loading

3. **New API Routes**
   - `frontend/app/api/mcp-configs/[userId]/route.ts` - Proxy to backend MCP config endpoints
   - `frontend/app/api/mcp-templates/route.ts` - Proxy to backend templates endpoint
   - Updated `frontend/app/api/tools/route.ts` - Support user_id parameter

## Configuration Storage

User configurations are stored in S3 with the following structure:

```
{sessions_bucket}/mcp-configs/user_{user_id}/config.json
```

Example configuration:

```json
{
  "servers": [
    {
      "name": "GitHub Integration",
      "command": "uvx",
      "args": ["mcp-server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxxxxxxxxxxx",
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "description": "GitHub repository operations"
    }
  ],
  "updated_at": "2025-01-01T00:00:00Z"
}
```

## Predefined Templates

The system includes templates for common MCP servers:

1. **AWS Documentation** (default)

   - Official AWS documentation MCP server
   - Command: `uvx awslabs.aws-documentation-mcp-server@latest`

2. **Filesystem**

   - File system operations
   - Command: `uvx mcp-server-filesystem`

3. **GitHub**

   - GitHub repository operations
   - Command: `uvx mcp-server-github`
   - Requires: `GITHUB_PERSONAL_ACCESS_TOKEN`

4. **Web Search**
   - Brave web search integration
   - Command: `uvx mcp-server-brave-search`
   - Requires: `BRAVE_API_KEY`

## Usage

1. **Access Configuration**: Click the "MCP Servers" button in the chat interface
2. **Add Server**: Use "Add MCP Server" or select from templates
3. **Configure**: Fill in server details including environment variables
4. **Save**: Click "Save Configurations" to store in S3
5. **Use**: Your custom servers will be available immediately in new chat sessions

## Security Considerations

- Configurations are stored per-user with S3 prefix isolation
- Environment variables (like API keys) are stored in S3
- Consider implementing encryption at rest for sensitive data
- Validate MCP server commands to prevent security issues

## Development

To test locally:

1. Ensure your backend has S3 access configured
2. Set the `SESSIONS_BUCKET_NAME` environment variable
3. Start both backend and frontend
4. Configure MCP servers through the UI

## Troubleshooting

- Check backend logs for MCP client initialization errors
- Verify S3 permissions for the sessions bucket
- Ensure MCP server commands are available in the environment
- Check environment variables are properly configured
