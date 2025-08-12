import { NextRequest, NextResponse } from 'next/server';

export async function DELETE(request: NextRequest, { params }: { params: { userId: string; sessionId: string } }) {
  try {
    const { userId, sessionId } = params;

    console.log('API route called to delete session:', { userId, sessionId });

    // Get the Backend URL from environment variable
    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;
    console.log('Backend URL:', BACKEND_URL);

    if (!BACKEND_URL) {
      throw new Error('NEXT_PUBLIC_BACKEND_URL environment variable is not set');
    }

    const backendUrl = `https://${BACKEND_URL}/session/${userId}/${sessionId}`;
    console.log('Making request to backend URL:', backendUrl);

    const response = await fetch(backendUrl, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    console.log('Response status:', response.status);

    if (!response.ok) {
      let errorMessage = `HTTP error! status: ${response.status}`;
      try {
        const errorData = await response.json();
        console.error('Error response data:', errorData);
        if (errorData.details) {
          errorMessage += ` - ${errorData.details}`;
        }
        if (errorData.error) {
          errorMessage += ` - ${errorData.error}`;
        }
      } catch (parseError) {
        console.error('Failed to parse error response as JSON:', parseError);
        const errorText = await response.text();
        console.error('Error response text:', errorText);
        if (errorText) {
          errorMessage += ` - ${errorText}`;
        }
      }
      throw new Error(errorMessage);
    }

    const result = await response.json();
    console.log('Session deletion result:', result);

    return NextResponse.json(result, { status: 200 });
  } catch (error) {
    console.error('Error deleting session:', error);
    return NextResponse.json(
      {
        error: 'Failed to delete session',
        details: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
