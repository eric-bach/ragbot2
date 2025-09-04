import { NextRequest, NextResponse } from 'next/server';
import { getBackendUrl } from '../../utils/backend-url';

const BACKEND_URL = getBackendUrl();

export async function GET(request: NextRequest, { params }: { params: { userId: string } }) {
  try {
    const { userId } = params;

    const response = await fetch(`${BACKEND_URL}/mcp-configs/${userId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching MCP configs:', error);
    return NextResponse.json({ error: 'Failed to fetch MCP configurations' }, { status: 500 });
  }
}

export async function POST(request: NextRequest, { params }: { params: { userId: string } }) {
  try {
    const { userId } = params;
    const configs = await request.json();

    console.log('Saving MCP configs for user:', userId);
    console.log('Configs payload:', JSON.stringify(configs, null, 2));

    const response = await fetch(`${BACKEND_URL}/mcp-configs/${userId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(configs),
    });

    const responseText = await response.text();
    console.log('Backend response status:', response.status);
    console.log('Backend response:', responseText);

    if (!response.ok) {
      let errorDetail = `Backend responded with status: ${response.status}`;
      try {
        const errorData = JSON.parse(responseText);
        errorDetail = errorData.detail || errorData.message || errorDetail;
      } catch (e) {
        errorDetail = responseText || errorDetail;
      }
      throw new Error(errorDetail);
    }

    const data = JSON.parse(responseText);
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error saving MCP configs:', error);
    return NextResponse.json(
      {
        error: 'Failed to save MCP configurations',
        details: error instanceof Error ? error.message : String(error),
      },
      { status: 500 }
    );
  }
}

export async function DELETE(request: NextRequest, { params }: { params: { userId: string } }) {
  try {
    const { userId } = params;

    const response = await fetch(`${BACKEND_URL}/mcp-configs/${userId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error deleting MCP configs:', error);
    return NextResponse.json({ error: 'Failed to delete MCP configurations' }, { status: 500 });
  }
}
