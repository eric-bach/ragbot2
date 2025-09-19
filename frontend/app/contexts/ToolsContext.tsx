'use client';

// Custom event for tools refresh
export const TOOLS_REFRESH_EVENT = 'tools-refresh';

export function triggerToolsRefresh() {
  console.log('Triggering tools refresh event...');
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent(TOOLS_REFRESH_EVENT));
  }
}
