import { NextRequest } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    console.log('API route called, parsing request body...');
    const body = await request.json();
    console.log('Request body:', body);

    // Get the ALB DNS name from environment variable
    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;
    if (!BACKEND_URL) {
      throw new Error('NEXT_PUBLIC_BACKEND_URL environment variable is not set');
    }

    // Determine the protocol and construct the URL
    const protocol = BACKEND_URL.includes('localhost') || BACKEND_URL.includes('127.0.0.1') ? 'http' : 'https';
    const backendUrl = `${protocol}://${BACKEND_URL}/chat`;

    console.log('Making request to backend URL:', backendUrl);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      console.log('Request timed out after 30 seconds');
      controller.abort();
    }, 30000); // 30 second timeout

    const fetchOptions = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/plain',
        'User-Agent': 'RAGBot-Frontend/1.0',
      },
      body: JSON.stringify({
        query: body.query,
        user_id: body.user_id,
        session_id: body.session_id, // Pass session_id to backend
        selected_tools: body.selected_tools, // Pass selected tools to backend
      }),
      signal: controller.signal,
    };

    console.log('Fetch options:', {
      method: fetchOptions.method,
      headers: fetchOptions.headers,
      bodyLength: JSON.stringify(body).length,
      hasSignal: !!fetchOptions.signal,
      sessionId: body.session_id,
    });

    const response = await fetch(backendUrl, fetchOptions);

    clearTimeout(timeoutId);

    console.log('RAGBot API response status:', response.status);
    console.log('RAGBot API response headers:', Object.fromEntries(response.headers.entries()));
    console.log('Response ok:', response.ok);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('RAGBot API error response:', errorText);
      return new Response(JSON.stringify({ error: 'Backend service error', details: errorText }), {
        status: response.status,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    console.log('Response body type:', typeof response.body);

    // Return the response directly with proper streaming headers
    return new Response(response.body, {
      status: 200,
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        Pragma: 'no-cache',
        Expires: '0',
        'Transfer-Encoding': 'chunked',
        Connection: 'keep-alive',
        'X-Accel-Buffering': 'no', // Disable nginx buffering
      },
    });
  } catch (error) {
    console.error('Error in chat API route:', error);
    return new Response(
      JSON.stringify({
        error: 'Internal server error',
        details: error instanceof Error ? error.message : 'Unknown error',
      }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
}
