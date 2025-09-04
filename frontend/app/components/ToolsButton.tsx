'use client';

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { Wrench, Check, Settings } from 'lucide-react';

interface Tool {
  name: string;
  description?: string;
  source?: string;
}

interface ToolsButtonProps {
  tools: Tool[];
  loading: boolean;
  error: string | null;
  selectedTools?: string[];
  onToolsChange?: (tools: string[]) => void;
  allowSelection?: boolean;
}

export default function ToolsButton({
  tools,
  loading,
  error,
  selectedTools = [],
  onToolsChange,
  allowSelection = false,
}: ToolsButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Use selectedTools directly from props instead of local state
  const currentSelectedTools = useMemo(() => selectedTools || [], [selectedTools]);

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

  const handleToolToggle = useCallback(
    (toolName: string) => {
      if (!allowSelection || !onToolsChange) return;

      const newSelection = currentSelectedTools.includes(toolName)
        ? currentSelectedTools.filter((t) => t !== toolName)
        : [...currentSelectedTools, toolName];

      onToolsChange(newSelection);
    },
    [allowSelection, onToolsChange, currentSelectedTools]
  );

  const allTools = tools;

  return (
    <div className='relative' ref={dropdownRef}>
      <button
        type='button'
        onClick={() => setIsOpen(!isOpen)}
        className='flex items-center space-x-1 text-muted-foreground hover:text-foreground transition-colors'
        title={allowSelection ? 'Select Tools for Query' : 'Available Tools'}
      >
        {allowSelection ? <Settings size={14} /> : <Wrench size={14} />}
        <span className='text-xs'>
          {allowSelection
            ? currentSelectedTools.length > 0
              ? `Tools (${currentSelectedTools.length} selected)`
              : 'Select Tools'
            : `Tools (${allTools.length})`}
        </span>
      </button>

      {isOpen && (
        <div className='absolute bottom-full left-0 mb-2 w-96 bg-background border border-border rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto'>
          <div className='p-3 border-b border-border'>
            <h3 className='font-semibold text-sm'>
              {loading
                ? 'Loading Tools...'
                : error
                ? 'Tools Error'
                : allowSelection
                ? `Select Tools (${currentSelectedTools.length}/${tools.length} selected)`
                : `Available Tools (${tools.length})`}
            </h3>
            {allowSelection && (
              <p className='text-xs text-muted-foreground mt-1'>
                Click tools to select which ones the agent should use for this query
              </p>
            )}
          </div>
          <div className='p-3 space-y-3'>
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
                <div
                  key={tool.name}
                  className={`text-sm border-b border-border last:border-b-0 pb-3 last:pb-0 ${
                    allowSelection ? 'cursor-pointer hover:bg-muted/50 p-2 rounded' : ''
                  }`}
                  onClick={() => allowSelection && handleToolToggle(tool.name)}
                >
                  <div className='flex items-center justify-between mb-1'>
                    <div className='flex items-center space-x-2'>
                      {allowSelection && (
                        <div
                          className={`w-4 h-4 border rounded flex items-center justify-center ${
                            currentSelectedTools.includes(tool.name) ? 'bg-blue-600 border-blue-600' : 'border-gray-300'
                          }`}
                        >
                          {currentSelectedTools.includes(tool.name) && <Check size={12} className='text-white' />}
                        </div>
                      )}
                      <div className='font-medium text-foreground'>{tool.name}</div>
                    </div>
                    {tool.source && (
                      <span
                        className={`text-xs px-2 py-1 rounded-full ${
                          tool.source === 'aws'
                            ? 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300'
                            : 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                        }`}
                      >
                        {tool.source}
                      </span>
                    )}
                  </div>
                  {tool.description && <div className='text-xs text-muted-foreground'>{tool.description}</div>}
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
