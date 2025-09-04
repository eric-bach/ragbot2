/**
 * Utility function to get the properly formatted backend URL
 */
export function getBackendUrl(): string {
  const url = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:3000';

  // If URL doesn't start with http:// or https://, assume https://
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    // Use http for localhost, https for everything else
    const protocol = url.includes('localhost') || url.includes('127.0.0.1') ? 'http' : 'https';
    return `${protocol}://${url}`;
  }

  return url;
}
