import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const envVars = {
      NEXT_PUBLIC_ALB_DNS_NAME: process.env.NEXT_PUBLIC_ALB_DNS_NAME,
      NODE_ENV: process.env.NODE_ENV,
      VERCEL_ENV: process.env.VERCEL_ENV,
      AMPLIFY_ENV: process.env.AMPLIFY_ENV,
      allNextPublicVars: Object.keys(process.env).filter((key) => key.startsWith('NEXT_PUBLIC_')),
      allEnvVars: Object.keys(process.env),
    };

    console.log('Debug endpoint called, environment variables:', envVars);

    return NextResponse.json({
      message: 'Debug endpoint working',
      environment: envVars,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Error in debug endpoint:', error);
    return NextResponse.json(
      {
        error: 'Debug endpoint error',
        details: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
