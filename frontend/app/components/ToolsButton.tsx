'use client';

import { useState, useEffect, useRef } from 'react';
import { Wrench } from 'lucide-react';

interface Tool {
  name: string;
}

interface ToolsButtonProps {
  tools: Tool[];
  loading: boolean;
  error: string | null;
}

export default function ToolsButton({ tools, loading, error }: ToolsButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Since tools no longer have categories, just use a simple list
  const allTools = tools;

  return (
    <div className='relative' ref={dropdownRef}>
      <button
        type='button'
        onClick={() => setIsOpen(!isOpen)}
        className='flex items-center space-x-1 text-muted-foreground hover:text-foreground transition-colors'
        title='Available Tools'
      >
        <Wrench size={14} />
        <span className='text-xs'>Tools ({allTools.length})</span>
      </button>

      {isOpen && (
        <div className='absolute bottom-full left-0 mb-2 w-80 bg-background border border-border rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto'>
          <div className='p-3 border-b border-border'>
            <h3 className='font-semibold text-sm'>
              {loading ? 'Loading Tools...' : error ? 'Tools Error' : `Available Tools (${tools.length})`}
            </h3>
          </div>
          <div className='p-3 space-y-4'>
            {loading && (
              <div className='flex items-center justify-center py-4'>
                <div className='animate-spin rounded-full h-4 w-4 border-b-2 border-current'></div>
                <span className='ml-2 text-sm text-muted-foreground'>Loading tools...</span>
              </div>
            )}

            {error && (
              <div className='text-sm text-red-600'>
                <div className='font-medium mb-1'>Failed to load tools</div>
                <div className='text-xs text-muted-foreground'>{error}</div>
              </div>
            )}

            {!loading &&
              !error &&
              allTools.map((tool) => (
                <div key={tool.name} className='text-sm'>
                  <div className='text-foreground'>{tool.name}</div>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
