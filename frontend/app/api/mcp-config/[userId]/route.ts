import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest, { params }: { params: { userId: string } }) {
  try {
    const { userId } = params;

    // Get the ALB DNS name from environment variable
    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;
    if (!BACKEND_URL) {
      throw new Error('NEXT_PUBLIC_BACKEND_URL environment variable is not set');
    }

    // Determine the protocol and construct the URL
    const protocol = BACKEND_URL.includes('localhost') || BACKEND_URL.includes('127.0.0.1') ? 'http' : 'https';
    const backendUrl = `${protocol}://${BACKEND_URL}`;

    const response = await fetch(`${backendUrl}/mcp-config/${userId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('MCP Config API error response:', errorText);
      throw new Error(`Backend responded with status: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching MCP config:', error);
    return NextResponse.json(
      {
        success: false,
        message: 'Failed to fetch MCP configuration',
        details: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest, { params }: { params: { userId: string } }) {
  try {
    const { userId } = params;
    const body = await request.json();

    // Get the ALB DNS name from environment variable
    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;
    if (!BACKEND_URL) {
      throw new Error('NEXT_PUBLIC_BACKEND_URL environment variable is not set');
    }

    // Determine the protocol and construct the URL
    const protocol = BACKEND_URL.includes('localhost') || BACKEND_URL.includes('127.0.0.1') ? 'http' : 'https';
    const backendUrl = `${protocol}://${BACKEND_URL}`;

    const response = await fetch(`${backendUrl}/mcp-config/${userId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('MCP Config POST API error response:', errorText);
      throw new Error(`Backend responded with status: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error saving MCP config:', error);
    return NextResponse.json(
      {
        success: false,
        message: 'Failed to save MCP configuration',
        details: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}

export async function DELETE(request: NextRequest, { params }: { params: { userId: string } }) {
  try {
    const { userId } = params;

    // Get the ALB DNS name from environment variable
    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;
    if (!BACKEND_URL) {
      throw new Error('NEXT_PUBLIC_BACKEND_URL environment variable is not set');
    }

    // Determine the protocol and construct the URL
    const protocol = BACKEND_URL.includes('localhost') || BACKEND_URL.includes('127.0.0.1') ? 'http' : 'https';
    const backendUrl = `${protocol}://${BACKEND_URL}`;

    const response = await fetch(`${backendUrl}/mcp-config/${userId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('MCP Config DELETE API error response:', errorText);
      throw new Error(`Backend responded with status: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error deleting MCP config:', error);
    return NextResponse.json(
      {
        success: false,
        message: 'Failed to delete MCP configuration',
        details: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
