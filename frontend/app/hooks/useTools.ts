import { useState, useEffect } from 'react';

interface Tool {
  name: string;
}

interface ToolsResponse {
  tools: Tool[];
  total_count: number;
}

interface HealthResponse {
  STATUS: string;
  AWS_REGION: string;
  KNOWLEDGE_BASE_ID: string;
  LINKUP_API_KEY: string;
}

export function useTools(userId?: string) {
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Don't fetch tools if we don't have a userId yet
    if (!userId) {
      return;
    }

    const fetchTools = async () => {
      // Add a shorter startup delay to give the backend time to initialize
      console.log('Waiting for backend to initialize...');
      await new Promise((resolve) => setTimeout(resolve, 1000)); // 1 second delay instead of 3

      const maxRetries = 3;
      const retryDelay = 2000; // 2 seconds

      for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
          console.log(`Attempt ${attempt}/${maxRetries}: Checking backend health...`);

          // First check if the backend is healthy
          const healthResponse = await fetch('/api/health');
          if (!healthResponse.ok) {
            throw new Error(`Backend is not healthy (status: ${healthResponse.status})`);
          }

          const healthData: HealthResponse = await healthResponse.json();
          console.log('Backend health check passed:', healthData);

          // Then fetch tools for the specific user (includes MCP tools)
          console.log(`Fetching tools for user ${userId}...`);
          const response = await fetch(`/api/tools/${userId}`);
          if (!response.ok) {
            throw new Error(`Could not list tools (status: ${response.status})`);
          }
          const data: ToolsResponse = await response.json();
          console.log(`Successfully loaded ${data.tools.length} tools`);
          setTools(data.tools);
          setError(null);
          break; // Success, exit retry loop
        } catch (err) {
          const errorMessage = err instanceof Error ? err.message : 'Could not list tools';
          console.error(`Attempt ${attempt}/${maxRetries} failed:`, errorMessage);

          if (attempt === maxRetries) {
            // Final attempt failed
            setError(`Failed after ${maxRetries} attempts: ${errorMessage}`);
          } else {
            // Wait before retrying
            console.log(`Retrying in ${retryDelay}ms...`);
            await new Promise((resolve) => setTimeout(resolve, retryDelay));
          }
        }
      }

      setLoading(false);
    };

    fetchTools();
  }, [userId]);

  return { tools, loading, error };
}
