import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ userId: string; sessionId: string }> }
) {
  try {
    console.log('Session GET API route called');

    const { userId, sessionId } = await params;

    if (!userId || !sessionId) {
      console.error('Missing userId or sessionId in request');
      return NextResponse.json({ error: 'Missing userId or sessionId' }, { status: 400 });
    }

    console.log('Getting session:', { userId, sessionId });

    // Get the backend URL from environment variable
    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;
    if (!BACKEND_URL) {
      throw new Error('NEXT_PUBLIC_BACKEND_URL environment variable is not set');
    }

    // Determine the protocol and construct the URL
    const protocol = BACKEND_URL.includes('localhost') || BACKEND_URL.includes('127.0.0.1') ? 'http' : 'https';
    const backendUrl = `${protocol}://${BACKEND_URL}/session/${userId}/${sessionId}`;

    console.log('Making request to backend URL:', backendUrl);

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    console.log('Backend response status:', response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend error:', errorText);
      return NextResponse.json({ error: 'Failed to get session', details: errorText }, { status: response.status });
    }

    const result = await response.json();
    console.log('Session retrieved successfully:', result.session_id, 'with', result.messages?.length || 0, 'messages');

    return NextResponse.json(result);
  } catch (error) {
    console.error('Error in session GET API:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ userId: string; sessionId: string }> }
) {
  try {
    console.log('Session PUT API route called');

    const { userId, sessionId } = await params;
    const body = await request.json();

    if (!userId || !sessionId) {
      console.error('Missing userId or sessionId in request');
      return NextResponse.json({ error: 'Missing userId or sessionId' }, { status: 400 });
    }

    if (!body.title) {
      console.error('Missing title in request body');
      return NextResponse.json({ error: 'Missing title' }, { status: 400 });
    }

    console.log('Updating session title:', { userId, sessionId, title: body.title });

    // Get the backend URL from environment variable
    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;
    if (!BACKEND_URL) {
      throw new Error('NEXT_PUBLIC_BACKEND_URL environment variable is not set');
    }

    // Determine the protocol and construct the URL
    const protocol = BACKEND_URL.includes('localhost') || BACKEND_URL.includes('127.0.0.1') ? 'http' : 'https';
    const backendUrl = `${protocol}://${BACKEND_URL}/session/${userId}/${sessionId}/title`;

    console.log('Making request to backend URL:', backendUrl);

    const response = await fetch(backendUrl, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        title: body.title,
      }),
    });

    console.log('Backend response status:', response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend error:', errorText);
      return NextResponse.json(
        { error: 'Failed to update session title', details: errorText },
        { status: response.status }
      );
    }

    const result = await response.json();
    console.log('Session title updated successfully:', result);

    return NextResponse.json(result);
  } catch (error) {
    console.error('Error in session PUT API:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ userId: string; sessionId: string }> }
) {
  try {
    console.log('Session DELETE API route called');

    const { userId, sessionId } = await params;

    if (!userId || !sessionId) {
      console.error('Missing userId or sessionId in request');
      return NextResponse.json({ error: 'Missing userId or sessionId' }, { status: 400 });
    }

    console.log('Deleting session:', { userId, sessionId });

    // Get the backend URL from environment variable
    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;
    if (!BACKEND_URL) {
      throw new Error('NEXT_PUBLIC_BACKEND_URL environment variable is not set');
    }

    // Determine the protocol and construct the URL
    const protocol = BACKEND_URL.includes('localhost') || BACKEND_URL.includes('127.0.0.1') ? 'http' : 'https';
    const backendUrl = `${protocol}://${BACKEND_URL}/session/${userId}/${sessionId}`;

    console.log('Making request to backend URL:', backendUrl);

    const response = await fetch(backendUrl, {
      method: 'DELETE',
    });

    console.log('Backend response status:', response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend error:', errorText);
      return NextResponse.json({ error: 'Failed to delete session', details: errorText }, { status: response.status });
    }

    const result = await response.json();
    console.log('Session deleted successfully:', result);

    return NextResponse.json({ success: true, ...result });
  } catch (error) {
    console.error('Error in session DELETE API:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
