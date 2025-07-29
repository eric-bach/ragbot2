import { useState, useEffect } from 'react';

interface Tool {
  name: string;
}

interface ToolsResponse {
  tools: Tool[];
  total_count: number;
}

export function useTools() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTools = async () => {
      try {
        const response = await fetch('/api/tools');
        if (!response.ok) {
          throw new Error('Could not list tools');
        }
        const data: ToolsResponse = await response.json();
        setTools(data.tools);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Could not list tools');
      } finally {
        setLoading(false);
      }
    };

    fetchTools();
  }, []);

  return { tools, loading, error };
}
