import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    // Get the ALB DNS name from environment variable
    const albDnsName = process.env.NEXT_PUBLIC_ALB_DNS_NAME;
    if (!albDnsName) {
      throw new Error('NEXT_PUBLIC_ALB_DNS_NAME environment variable is not set');
    }

    const response = await fetch(`https://${albDnsName}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Health API error response:', errorText);
      throw new Error(`Backend health check failed with status: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error checking backend health:', error);
    return NextResponse.json({ error: 'Failed to check backend health', details: error instanceof Error ? error.message : 'Unknown error' }, { status: 500 });
  }
}
