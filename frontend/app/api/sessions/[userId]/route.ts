import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest, { params }: { params: Promise<{ userId: string }> }) {
  try {
    console.log('Sessions GET API route called');

    const { userId } = await params;

    if (!userId) {
      console.error('Missing userId in request');
      return NextResponse.json({ error: 'Missing userId' }, { status: 400 });
    }

    console.log('Listing sessions for user:', userId);

    // Get the backend URL from environment variable
    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;
    if (!BACKEND_URL) {
      throw new Error('NEXT_PUBLIC_BACKEND_URL environment variable is not set');
    }

    // Determine the protocol and construct the URL
    const protocol = BACKEND_URL.includes('localhost') || BACKEND_URL.includes('127.0.0.1') ? 'http' : 'https';
    const backendUrl = `${protocol}://${BACKEND_URL}/sessions/${userId}`;

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
      return NextResponse.json({ error: 'Failed to list sessions', details: errorText }, { status: response.status });
    }

    const result = await response.json();
    console.log('Sessions listed successfully:', result.sessions?.length || 0, 'sessions found');

    return NextResponse.json(result);
  } catch (error) {
    console.error('Error in sessions GET API:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest, { params }: { params: Promise<{ userId: string }> }) {
  try {
    console.log('Sessions POST API route called');

    const { userId } = await params;
    const body = await request.json();

    if (!userId) {
      console.error('Missing userId in request');
      return NextResponse.json({ error: 'Missing userId' }, { status: 400 });
    }

    console.log('Creating session for user:', userId, 'with title:', body.title);

    // Get the backend URL from environment variable
    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;
    if (!BACKEND_URL) {
      throw new Error('NEXT_PUBLIC_BACKEND_URL environment variable is not set');
    }

    // Determine the protocol and construct the URL
    const protocol = BACKEND_URL.includes('localhost') || BACKEND_URL.includes('127.0.0.1') ? 'http' : 'https';
    const backendUrl = `${protocol}://${BACKEND_URL}/session`;

    console.log('Making request to backend URL:', backendUrl);

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        title: body.title || 'New Chat',
      }),
    });

    console.log('Backend response status:', response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend error:', errorText);
      return NextResponse.json({ error: 'Failed to create session', details: errorText }, { status: response.status });
    }

    const result = await response.json();
    console.log('Session created successfully:', result.session_id);

    return NextResponse.json(result);
  } catch (error) {
    console.error('Error in sessions POST API:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
