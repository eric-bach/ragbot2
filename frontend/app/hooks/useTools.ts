import { useState, useEffect, useCallback } from 'react';

interface Tool {
  name: string;
  description?: string;
  source?: string;
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

  const fetchTools = useCallback(async () => {
    if (!userId) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

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

        // Then fetch user-specific tools
        console.log('Fetching user-specific tools...');
        const response = await fetch(`/api/tools/${userId}`);
        if (!response.ok) {
          // Fallback to general tools endpoint if user-specific fails
          console.log('User-specific tools failed, falling back to general tools...');
          const fallbackResponse = await fetch('/api/tools');
          if (!fallbackResponse.ok) {
            throw new Error(`Could not list tools (status: ${fallbackResponse.status})`);
          }
          const fallbackData: ToolsResponse = await fallbackResponse.json();
          console.log(`Successfully loaded ${fallbackData.tools.length} general tools`);
          setTools(fallbackData.tools);
          setError(null);
          break;
        }

        const data: ToolsResponse = await response.json();
        console.log(`Successfully loaded ${data.tools.length} user-specific tools`);
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
  }, [userId]);

  useEffect(() => {
    fetchTools();
  }, [fetchTools]);

  const refreshTools = useCallback(() => {
    fetchTools();
  }, [fetchTools]);

  return { tools, loading, error, refreshTools };
}
