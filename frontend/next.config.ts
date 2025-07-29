import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  /* config options here */
  experimental: {
    serverComponentsExternalPackages: [],
  },
  async headers() {
    return [
      {
        source: '/api/chat',
        headers: [
          {
            key: 'X-Accel-Buffering',
            value: 'no',
          },
          {
            key: 'Cache-Control',
            value: 'no-cache',
          },
          {
            key: 'Connection',
            value: 'keep-alive',
          },
        ],
      },
    ];
  },
};

export default nextConfig;
