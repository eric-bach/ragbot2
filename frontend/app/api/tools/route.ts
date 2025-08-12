import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // Get the Backend URL from environment variable
    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;
    if (!BACKEND_URL) {
      throw new Error('NEXT_PUBLIC_BACKEND_URL environment variable is not set');
    }

    // Determine the protocol and construct the URL
    const protocol = BACKEND_URL.includes('localhost') || BACKEND_URL.includes('127.0.0.1') ? 'http' : 'https';
    const backendUrl = `${protocol}://${BACKEND_URL}`;

    const response = await fetch(`${backendUrl}/tools`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Tools API error response:', errorText);
      throw new Error(`Backend responded with status: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching tools:', error);
    return NextResponse.json(
      { error: 'Failed to fetch tools', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
