import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    console.log('API route called, parsing request body...');
    const body = await request.json();
    console.log('Request body:', body);

    // Get the ALB DNS name from environment variable
    const albDnsName = process.env.NEXT_PUBLIC_ALB_DNS_NAME;
    console.log('ALB DNS Name:', albDnsName);

    if (!albDnsName) {
      throw new Error('NEXT_PUBLIC_ALB_DNS_NAME environment variable is not set');
    }

    const backendUrl = `https://${albDnsName}/chat`;
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
      body: JSON.stringify(body),
      signal: controller.signal,
    };

    console.log('Fetch options:', {
      method: fetchOptions.method,
      headers: fetchOptions.headers,
      bodyLength: JSON.stringify(body).length,
      hasSignal: !!fetchOptions.signal,
    });

    const response = await fetch(backendUrl, fetchOptions);

    clearTimeout(timeoutId);

    console.log('RAGBot API response status:', response.status);
    console.log('RAGBot API response headers:', Object.fromEntries(response.headers.entries()));
    console.log('Response ok:', response.ok);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('RAGBot API error response:', errorText);

      // Provide more specific error messages based on status code
      let errorMessage = `HTTP error! status: ${response.status}`;
      let errorType = 'HTTPError';

      if (response.status === 503) {
        errorMessage = 'Backend service is temporarily unavailable. Please try again in a moment.';
        errorType = 'ServiceUnavailable';
      } else if (response.status === 502) {
        errorMessage = 'Backend service is not responding. Please try again later.';
        errorType = 'BadGateway';
      } else if (response.status === 500) {
        errorMessage = 'Backend encountered an internal error. Please try again.';
        errorType = 'InternalServerError';
      } else if (errorText) {
        errorMessage += ` - ${errorText}`;
      }

      return NextResponse.json({ error: errorMessage, details: errorText, type: errorType }, { status: response.status });
    }

    // Stream the response directly to the frontend
    console.log('Setting up streaming response...');
    console.log('Response headers:', Object.fromEntries(response.headers.entries()));
    console.log('Response status:', response.status);
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
              console.log(`Streaming chunk ${chunkCount} to frontend, length:`, chunk.length, 'content:', chunk.substring(0, 100));
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
    console.error('Error proxying request to RAGBot API:', error);
    console.error('Error name:', error instanceof Error ? error.name : 'Unknown');
    console.error('Error message:', error instanceof Error ? error.message : 'Unknown');
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
        errorMessage = 'Network error - unable to reach RAGBot API. The backend service may be starting up.';
        errorType = 'NetworkError';
      } else if (error.message.includes('ENOTFOUND') || error.message.includes('ECONNREFUSED')) {
        errorMessage = 'Backend service is not available. Please try again in a moment.';
        errorType = 'ConnectionError';
      } else if (error.message.includes('getaddrinfo ENOTFOUND')) {
        errorMessage = 'Cannot resolve backend hostname. Please check your configuration.';
        errorType = 'DNSResolutionError';
      } else if (error.message.includes('ECONNRESET')) {
        errorMessage = 'Connection was reset by the backend. Please try again.';
        errorType = 'ConnectionResetError';
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
