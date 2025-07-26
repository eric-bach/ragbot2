# RAGBot2 with Bright Data Integration

This project integrates AWS Strands with Bright Data API for web search capabilities.

## Setup

### Quick Setup (Recommended)

Run the interactive setup script:

```bash
python setup.py
```

This will:

- Check and install dependencies
- Prompt you for your Bright Data API key
- Create a `.env` file with your configuration

### Manual Setup

#### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 2. Configure Bright Data API Credentials

**Option A: Create a .env file (Recommended)**
Create a `.env` file in your project root:

```bash
# Bright Data API Configuration
BRIGHT_DATA_API_KEY=your_actual_bright_data_api_key

# AWS Configuration (optional)
AWS_PROFILE=bach-dev
AWS_REGION=us-east-1
```

**Option B: Set Environment Variables**

Linux/macOS:

```bash
export BRIGHT_DATA_API_KEY=your_bright_data_api_key
```

Windows (PowerShell):

```powershell
$env:BRIGHT_DATA_API_KEY="your_bright_data_api_key"
```

Windows (Command Prompt):

```cmd
set BRIGHT_DATA_API_KEY=your_bright_data_api_key
```

#### 3. Configure AWS Credentials

Make sure you have AWS credentials configured for the `bach-dev` profile, or update the profile name in `agent.py`.

## Usage

Run the interactive agent:

```bash
python agent.py
```

### Available Tools

1. **bright_data_web_search**: Perform general web searches

   - Parameters: query, country, language, num_results, include_domains, exclude_domains

2. **bright_data_news_search**: Search for news articles

   - Parameters: query, country, language, num_results, time_period

3. **http_request**: Make HTTP requests (from strands-agents-tools)

### Example Usage

Once the agent is running, you can ask questions like:

- "Search for the latest news about artificial intelligence"
- "Find information about Python programming tutorials"
- "Search for recent developments in renewable energy"

## Bright Data API Features

- **Web Search**: Access to Google search results
- **News Search**: Access to news articles from various sources
- **Geo-targeting**: Search results from specific countries
- **Language filtering**: Results in specific languages
- **Domain filtering**: Include or exclude specific domains

## Error Handling

The tools include comprehensive error handling for:

- Missing API credentials
- Network timeouts
- API rate limits
- Invalid responses

## Notes

- The Bright Data API requires a paid subscription
- API calls are rate-limited based on your subscription plan
- Results are formatted for easy consumption by the AI agent
