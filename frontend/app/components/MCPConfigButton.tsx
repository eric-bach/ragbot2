'use client';

import { useState, useEffect } from 'react';
import { Settings, Plus, Trash2, Copy } from 'lucide-react';

interface MCPServerConfig {
  name: string;
  command: string;
  args: string[];
  env: Record<string, string>;
  description: string;
}

interface MCPConfigButtonProps {
  userId: string;
  onClose?: () => void;
  showAsButton?: boolean;
}

export default function MCPConfigButton({ userId, onClose, showAsButton = false }: MCPConfigButtonProps) {
  const [isOpen, setIsOpen] = useState(!showAsButton);
  const [configs, setConfigs] = useState<MCPServerConfig[]>([]);
  const [loading, setLoading] = useState(false);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);

  const [newConfig, setNewConfig] = useState<MCPServerConfig>({
    name: '',
    command: '',
    args: [],
    env: {},
    description: '',
  });

  const handleClose = () => {
    if (onClose) {
      onClose();
    } else {
      setIsOpen(false);
    }
  };

  const handleOpen = () => {
    setIsOpen(true);
    loadConfigs();
  };

  useEffect(() => {
    if (isOpen && !showAsButton) {
      loadConfigs();
    }
  }, [isOpen]);

  const loadConfigs = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/mcp-configs/${userId}`);
      if (response.ok) {
        const data = await response.json();
        setConfigs(data.servers || []);
      }
    } catch (error) {
      console.error('Failed to load MCP configs:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveConfigs = async () => {
    try {
      setLoading(true);

      console.log('Saving MCP configs...');
      console.log('Current configs state:', configs);
      console.log('Number of configs to save:', configs.length);

      if (configs.length === 0) {
        alert('No MCP configurations to save. Please add at least one configuration first.');
        return;
      }

      const response = await fetch(`/api/mcp-configs/${userId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(configs),
      });

      if (response.ok) {
        alert('MCP configurations saved successfully!');
      } else {
        const errorData = await response.json();
        const errorMessage = errorData.details || errorData.error || 'Failed to save configurations';
        throw new Error(errorMessage);
      }
    } catch (error) {
      console.error('Failed to save MCP configs:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to save configurations';
      alert(`Failed to save configurations: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const addConfig = () => {
    console.log('Adding new config:', newConfig);
    console.log('Current configs before adding:', configs);

    if (editingIndex !== null) {
      const updatedConfigs = [...configs];
      updatedConfigs[editingIndex] = newConfig;
      setConfigs(updatedConfigs);
      setEditingIndex(null);
      console.log('Updated existing config at index', editingIndex);
    } else {
      const newConfigs = [...configs, newConfig];
      setConfigs(newConfigs);
      console.log('Added new config. Total configs now:', newConfigs.length);
    }

    setNewConfig({
      name: '',
      command: '',
      args: [],
      env: {},
      description: '',
    });
  };

  const removeConfig = (index: number) => {
    setConfigs(configs.filter((_, i) => i !== index));
  };

  const editConfig = (index: number) => {
    setNewConfig(configs[index]);
    setEditingIndex(index);
  };

  const parseArrayInput = (value: string): string[] => {
    return value
      .split(',')
      .map((item) => item.trim())
      .filter((item) => item.length > 0);
  };

  const parseEnvInput = (value: string): Record<string, string> => {
    const env: Record<string, string> = {};
    value.split('\n').forEach((line) => {
      const [key, ...rest] = line.split('=');
      if (key && rest.length > 0) {
        env[key.trim()] = rest.join('=').trim();
      }
    });
    return env;
  };

  const formatEnvForDisplay = (env: Record<string, string>): string => {
    return Object.entries(env)
      .map(([key, value]) => `${key}=${value}`)
      .join('\n');
  };

  if (showAsButton && !isOpen) {
    return (
      <button
        onClick={handleOpen}
        className='flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-800 transition-colors'
        title='Configure MCP Servers'
      >
        <Settings size={16} />
        <span>MCP Servers</span>
      </button>
    );
  }

  if (!isOpen) {
    return null;
  }

  return (
    <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50'>
      <div className='bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden'>
        <div className='flex justify-between items-center p-6 border-b'>
          <h2 className='text-xl font-semibold'>MCP Server Configuration</h2>
          <button onClick={handleClose} className='text-gray-500 hover:text-gray-700'>
            ×
          </button>
        </div>

        <div className='p-6 overflow-y-auto max-h-[calc(90vh-120px)]'>
          {/* Existing Configurations */}
          <div className='mb-6'>
            <h3 className='text-lg font-medium mb-3'>Current Configurations</h3>
            {configs.length === 0 ? (
              <p className='text-gray-500'>No MCP servers configured</p>
            ) : (
              <div className='space-y-3'>
                {configs.map((config, index) => (
                  <div key={index} className='border rounded-lg p-4 bg-gray-50'>
                    <div className='flex justify-between items-start'>
                      <div className='flex-1'>
                        <h4 className='font-medium'>{config.name}</h4>
                        <p className='text-sm text-gray-600 mb-2'>{config.description}</p>
                        <div className='text-xs text-gray-500'>
                          <div>
                            Command: {config.command} {config.args.join(' ')}
                          </div>
                          {Object.keys(config.env).length > 0 && (
                            <div className='mt-1'>Environment: {Object.keys(config.env).join(', ')}</div>
                          )}
                        </div>
                      </div>
                      <div className='flex gap-2'>
                        <button
                          onClick={() => editConfig(index)}
                          className='text-blue-600 hover:text-blue-800'
                          title='Edit'
                        >
                          <Settings size={16} />
                        </button>
                        <button
                          onClick={() => removeConfig(index)}
                          className='text-red-600 hover:text-red-800'
                          title='Remove'
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Add/Edit Configuration Form */}
          <div className='mb-6'>
            <div className='space-y-4'>
              <div>
                <label className='block text-sm font-medium mb-1'>Name</label>
                <input
                  type='text'
                  value={newConfig.name}
                  onChange={(e) => setNewConfig({ ...newConfig, name: e.target.value })}
                  className='w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500'
                  placeholder='e.g., My Custom MCP Server'
                />
              </div>

              <div>
                <label className='block text-sm font-medium mb-1'>Description</label>
                <input
                  type='text'
                  value={newConfig.description}
                  onChange={(e) => setNewConfig({ ...newConfig, description: e.target.value })}
                  className='w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500'
                  placeholder='Brief description of what this server does'
                />
              </div>

              <div>
                <label className='block text-sm font-medium mb-1'>Command</label>
                <input
                  type='text'
                  value={newConfig.command}
                  onChange={(e) => setNewConfig({ ...newConfig, command: e.target.value })}
                  className='w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500'
                  placeholder='e.g., uvx, python, node'
                />
              </div>

              <div>
                <label className='block text-sm font-medium mb-1'>Arguments (comma-separated)</label>
                <input
                  type='text'
                  value={newConfig.args.join(', ')}
                  onChange={(e) => setNewConfig({ ...newConfig, args: parseArrayInput(e.target.value) })}
                  className='w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500'
                  placeholder='e.g., mcp-server-github, --port, 3000'
                />
              </div>

              <div>
                <label className='block text-sm font-medium mb-1'>
                  Environment Variables (key=value, one per line)
                </label>
                <textarea
                  value={formatEnvForDisplay(newConfig.env)}
                  onChange={(e) => setNewConfig({ ...newConfig, env: parseEnvInput(e.target.value) })}
                  className='w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500'
                  rows={3}
                  placeholder='GITHUB_TOKEN=your_token&#10;DEBUG=true'
                />
              </div>

              <button
                onClick={addConfig}
                disabled={!newConfig.name || !newConfig.command}
                className='flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed'
              >
                <Plus size={16} />
                {editingIndex !== null ? 'Update' : 'Add'} Server
              </button>

              {editingIndex !== null && (
                <button
                  onClick={() => {
                    setEditingIndex(null);
                    setNewConfig({
                      name: '',
                      command: '',
                      args: [],
                      env: {},
                      description: '',
                    });
                  }}
                  className='ml-2 px-4 py-2 text-gray-600 border rounded hover:bg-gray-50'
                >
                  Cancel
                </button>
              )}
            </div>
          </div>

          {/* Save Button */}
          <div className='flex justify-end gap-3 pt-4 border-t'>
            <button onClick={handleClose} className='px-4 py-2 text-gray-600 border rounded hover:bg-gray-50'>
              Cancel
            </button>
            <button
              onClick={saveConfigs}
              disabled={loading || configs.length === 0}
              className={`px-4 py-2 text-white rounded ${
                configs.length === 0
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-green-600 hover:bg-green-700 disabled:bg-gray-400'
              }`}
              title={configs.length === 0 ? 'Add at least one configuration first' : ''}
            >
              {loading ? 'Saving...' : `Save ${configs.length} Configuration${configs.length !== 1 ? 's' : ''}`}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
