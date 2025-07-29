import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    console.log('API route called, parsing request body...');
    const body = await request.json();
    console.log('Request body:', body);

    console.log('Making request to RAGBot API...');
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

    //const response = await fetch('http://localhost:8000/chat', { // Local Docker - WORKING
    //const response = await fetch('http://54.162.125.152:8000/chat', { // ECS Container - WORKING
    const response = await fetch('https://ragbot2.ericbach.dev/chat', {
      // AWS ALB - WORKING
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    console.log('RAGBot API response status:', response.status);
    console.log('RAGBot API response headers:', Object.fromEntries(response.headers.entries()));

    if (!response.ok) {
      const errorText = await response.text();
      console.error('RAGBot API error response:', errorText);
      return NextResponse.json({ error: `HTTP error! status: ${response.status}`, details: errorText }, { status: response.status });
    }

    // Stream the response directly to the frontend
    console.log('Setting up streaming response...');

    const stream = new ReadableStream({
      async start(controller) {
        const reader = response.body?.getReader();
        if (!reader) {
          controller.error(new Error('No response body reader available'));
          return;
        }

        const decoder = new TextDecoder();

        try {
          while (true) {
            const { done, value } = await reader.read();

            if (done) {
              console.log('Streaming complete');
              controller.close();
              break;
            }

            if (value) {
              const chunk = decoder.decode(value, { stream: true });
              console.log('Streaming chunk to frontend, length:', chunk.length);
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
      },
    });
  } catch (error) {
    console.error('Error proxying request to RAGBot API:', error);
    console.error('Error stack:', error instanceof Error ? error.stack : 'No stack trace');

    let errorMessage = 'Failed to process request';
    let errorType = 'Unknown error';

    if (error instanceof Error) {
      errorMessage = error.message;
      errorType = error.constructor.name;

      // Handle specific error types
      if (error.name === 'AbortError') {
        errorMessage = 'Request timed out after 30 seconds';
        errorType = 'TimeoutError';
      } else if (error.message.includes('fetch')) {
        errorMessage = 'Network error - unable to reach RAGBot API';
        errorType = 'NetworkError';
      }
    }

    return NextResponse.json(
      {
        error: 'Failed to process request',
        details: errorMessage,
        type: errorType,
      },
      { status: 500 }
    );
  }
}
