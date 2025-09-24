import { NextRequest, NextResponse } from 'next/server';

// This route is deprecated - use /api/sessions/[userId]/[sessionId] instead
// Keeping for backward compatibility
export async function DELETE(request: NextRequest) {
  try {
    console.log('Legacy Session DELETE API route called - consider using /api/sessions/[userId]/[sessionId]');

    // Extract userId and sessionId from URL search params
    const { searchParams } = new URL(request.url);
    const userId = searchParams.get('userId');
    const sessionId = searchParams.get('sessionId');

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

    console.log('Making DELETE request to backend URL:', backendUrl);

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
