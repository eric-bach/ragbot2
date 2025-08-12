import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    console.log('API route called, parsing request body...');
    const body = await request.json();
    console.log('Request body:', body);

    // Get the Backend URL from environment variable
    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;
    console.log('Backend URL:', BACKEND_URL);

    if (!BACKEND_URL) {
      throw new Error('NEXT_PUBLIC_BACKEND_URL environment variable is not set');
    }

    const backendUrl = `https://${BACKEND_URL}/chat`;
    console.log('Making request to backend URL:', backendUrl);

    console.log('Making request to RAGBot API...');
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      console.log('Request timed out after 30 seconds');
      controller.abort();
    }, 30000); // 30 second timeout

    const fetchOptions = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: body.query,
        user_id: body.user_id,
        session_id: body.session_id, // Pass session_id to backend
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
      return NextResponse.json({ error: 'Backend service error', details: errorText }, { status: response.status });
    }

    console.log('Response body type:', typeof response.body);

    const stream = new ReadableStream({
      async start(controller) {
        const reader = response.body?.getReader();
        if (!reader) {
          console.error('No response body reader available');
          controller.error(new Error('No response body reader available'));
          return;
        }

        const decoder = new TextDecoder();

        try {
          let chunkCount = 0;
          while (true) {
            const { done, value } = await reader.read();

            if (done) {
              console.log('Streaming complete, total chunks:', chunkCount);
              controller.close();
              break;
            }

            if (value) {
              chunkCount++;
              const chunk = decoder.decode(value, { stream: true });
              console.log(
                `Streaming chunk ${chunkCount} to frontend, length:`,
                chunk.length,
                'content:',
                chunk.substring(0, 100)
              );
              controller.enqueue(new TextEncoder().encode(chunk));
            }
          }
        } catch (error) {
          console.error('Error in streaming:', error);
          controller.error(error);
        } finally {
          reader.releaseLock();
        }
      },
    });

    return new Response(stream, {
      status: 200,
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Cache-Control': 'no-cache',
        Connection: 'keep-alive',
        'X-Accel-Buffering': 'no', // Disable nginx buffering
        'Transfer-Encoding': 'chunked',
      },
    });
  } catch (error) {
    console.error('Error in chat API route:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
