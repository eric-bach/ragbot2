'use client';

import { useState } from 'react';
import { Settings, Check } from 'lucide-react';

interface Tool {
  name: string;
  description?: string;
  source?: string;
}

interface ToolSelectorProps {
  tools: Tool[];
  selectedTools: string[];
  onToolSelectionChange: (selectedTools: string[]) => void;
  loading?: boolean;
}

export default function ToolSelector({ tools, selectedTools, onToolSelectionChange, loading }: ToolSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);

  const handleToolToggle = (toolName: string) => {
    const newSelection = selectedTools.includes(toolName)
      ? selectedTools.filter((t) => t !== toolName)
      : [...selectedTools, toolName];

    onToolSelectionChange(newSelection);
  };

  const handleSelectAll = () => {
    if (selectedTools.length === tools.length) {
      onToolSelectionChange([]);
    } else {
      onToolSelectionChange(tools.map((t) => t.name));
    }
  };

  const getToolSourceColor = (source?: string) => {
    switch (source) {
      case 'aws':
        return 'text-orange-600 bg-orange-50';
      case 'user_mcp':
        return 'text-purple-600 bg-purple-50';
      case 'base':
        return 'text-blue-600 bg-blue-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getToolSourceLabel = (source?: string) => {
    switch (source) {
      case 'aws':
        return 'AWS';
      case 'user_mcp':
        return 'MCP';
      case 'base':
        return 'Base';
      default:
        return 'Unknown';
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className='flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-800 transition-colors'
        title='Select Tools'
        disabled={loading}
      >
        <Settings size={16} />
        <span>Tools ({selectedTools.length > 0 ? selectedTools.length : 'All'})</span>
      </button>
    );
  }

  return (
    <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50'>
      <div className='bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden'>
        <div className='flex justify-between items-center p-6 border-b'>
          <h2 className='text-xl font-semibold'>Select Tools</h2>
          <button onClick={() => setIsOpen(false)} className='text-gray-500 hover:text-gray-700'>
            ×
          </button>
        </div>

        <div className='p-6 overflow-y-auto max-h-[calc(80vh-120px)]'>
          <div className='mb-4'>
            <p className='text-sm text-gray-600 mb-3'>
              Choose which tools the AI agent should use. If no tools are selected, all available tools will be used.
            </p>

            <div className='flex items-center justify-between mb-4'>
              <span className='text-sm font-medium'>
                {selectedTools.length} of {tools.length} tools selected
              </span>
              <button onClick={handleSelectAll} className='text-sm text-blue-600 hover:text-blue-800'>
                {selectedTools.length === tools.length ? 'Deselect All' : 'Select All'}
              </button>
            </div>
          </div>

          <div className='space-y-2'>
            {tools.map((tool, index) => (
              <div
                key={index}
                className={`flex items-center p-3 border rounded-lg cursor-pointer transition-colors ${
                  selectedTools.includes(tool.name)
                    ? 'bg-blue-50 border-blue-200'
                    : 'bg-white border-gray-200 hover:bg-gray-50'
                }`}
                onClick={() => handleToolToggle(tool.name)}
              >
                <div className='flex-shrink-0 mr-3'>
                  <div
                    className={`w-5 h-5 border-2 rounded flex items-center justify-center ${
                      selectedTools.includes(tool.name) ? 'bg-blue-600 border-blue-600' : 'border-gray-300'
                    }`}
                  >
                    {selectedTools.includes(tool.name) && <Check size={12} className='text-white' />}
                  </div>
                </div>

                <div className='flex-1 min-w-0'>
                  <div className='flex items-center gap-2 mb-1'>
                    <h3 className='font-medium truncate'>{tool.name}</h3>
                    {tool.source && (
                      <span className={`text-xs px-2 py-1 rounded-full ${getToolSourceColor(tool.source)}`}>
                        {getToolSourceLabel(tool.source)}
                      </span>
                    )}
                  </div>
                  {tool.description && <p className='text-sm text-gray-600 line-clamp-2'>{tool.description}</p>}
                </div>
              </div>
            ))}
          </div>

          {tools.length === 0 && (
            <div className='text-center py-8'>
              <p className='text-gray-500'>No tools available</p>
            </div>
          )}
        </div>

        <div className='flex justify-end gap-3 p-6 border-t'>
          <button onClick={() => setIsOpen(false)} className='px-4 py-2 text-gray-600 border rounded hover:bg-gray-50'>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
