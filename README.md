# RAGBot2 with LinkUp Integration

This project integrates AWS Strands with LinkUp API for web search capabilities.

## Setup

### Quick Setup (Recommended)

Run the interactive setup script:

```bash
python setup.py
```

This will:

- Check and install dependencies
- Prompt you for your LinkUp API key
- Create a `.env` file with your configuration

### Manual Setup

#### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 2. Configure LinkUp API Credentials

**Option A: Create a .env file (Recommended)**
Create a `.env` file in your project root:

```bash
# LinkUp API Configuration
LINKUP_API_KEY=your_actual_linkup_api_key

# AWS Configuration (optional)
AWS_PROFILE=bach-dev
AWS_REGION=us-east-1
```

**Option B: Set Environment Variables**

Linux/macOS:

```bash
export LINKUP_API_KEY=your_linkup_api_key
```

Windows (PowerShell):

```powershell
$env:LINKUP_API_KEY="your_linkup_api_key"
```

Windows (Command Prompt):

```cmd
set LINKUP_API_KEY=your_linkup_api_key
```

#### 3. Configure AWS Credentials

Make sure you have AWS credentials configured for the `bach-dev` profile, or update the profile name in `agent.py`.

## Usage

Run the interactive agent:

```bash
python agent.py
```

### Available Tools

1. **web_search**: Perform web searches using LinkUp's Web Search API

   - Parameters: query (search query to perform)
   - Returns: Sourced answers with references from LinkUp API

2. **AWS Documentation**: Lookup AWS documentation (from aws-documentation-mcp-server)

### Example Usage

Once the agent is running, you can ask questions like:

- "Search for the latest news about artificial intelligence"
- "Find information about Python programming tutorials"
- "Search for recent developments in renewable energy"
- "What is the current price of bitcoin?"

## LinkUp API Features

- **Web Search**: Access to comprehensive web search results
- **Sourced Answers**: Results include source references for verification
- **Standard Depth**: Provides thorough search coverage
- **Structured Output**: Results formatted for easy consumption by the AI agent

## Error Handling

The tools include comprehensive error handling for:

- Missing API credentials
- Network timeouts
- API rate limits
- Invalid responses

## Notes

- The LinkUp API requires a paid subscription
- API calls are rate-limited based on your subscription plan
- Results are formatted for easy consumption by the AI agent
