'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Plus, Trash2, Save, X, Settings, Wrench, RefreshCw } from 'lucide-react';

interface MCPServerConfig {
  name: string;
  description?: string;
  server_type: 'stdio' | 'sse' | 'websocket';
  command?: string;
  args?: string[];
  url?: string;
  env_vars?: Record<string, string>;
  enabled: boolean;
}

interface MCPError {
  server_name: string;
  error: string;
  type: string;
}

interface MCPTool {
  name: string;
  description?: string;
  source?: string;
}

interface MCPConfigModalProps {
  userId: string;
  isOpen: boolean;
  onClose: () => void;
  onConfigsSaved?: () => void;
}

export default function MCPConfigModal({ userId, isOpen, onClose, onConfigsSaved }: MCPConfigModalProps) {
  const [configs, setConfigs] = useState<MCPServerConfig[]>([]);
  const [envVarsInput, setEnvVarsInput] = useState<Record<number, string>>({});
  const [tools, setTools] = useState<MCPTool[]>([]);
  const [mcpErrors, setMcpErrors] = useState<MCPError[]>([]);
  const [showTools, setShowTools] = useState(false);
  const [loadingTools, setLoadingTools] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadConfigs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/mcp-config/${userId}`);
      const data = await response.json();

      if (data.success) {
        setConfigs(data.servers || []);
        // Initialize envVarsInput state
        const envInputs: Record<number, string> = {};
        (data.servers || []).forEach((server: MCPServerConfig, index: number) => {
          envInputs[index] = Object.entries(server.env_vars || {})
            .map(([k, v]) => `${k}=${v}`)
            .join('\n');
        });
        setEnvVarsInput(envInputs);
      } else {
        setError('Failed to load configurations');
      }
    } catch (err) {
      setError('Failed to load configurations');
      console.error('Error loading MCP configs:', err);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    if (isOpen && userId) {
      loadConfigs();
    }
  }, [isOpen, userId, loadConfigs]);

  const loadTools = async () => {
    setLoadingTools(true);
    setError(null);
    setMcpErrors([]);
    try {
      const response = await fetch(`/api/tools/${userId}`);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Tools API error:', errorText);
        throw new Error(`Failed to load tools: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      setTools(data.tools || []);
      setMcpErrors(data.mcp_errors || []);
      setShowTools(true);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load tools';
      setError(errorMessage);
      console.error('Error loading tools:', err);
    } finally {
      setLoadingTools(false);
    }
  };

  const saveConfigs = async () => {
    setSaving(true);
    setError(null);
    try {
      const response = await fetch(`/api/mcp-config/${userId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ servers: configs }),
      });

      const data = await response.json();

      if (data.success) {
        // Load tools after successful save
        await loadTools();
        // Notify parent component that configs were saved
        console.log('MCP configs saved successfully, triggering tools refresh...');
        onConfigsSaved?.();
      } else {
        setError('Failed to save configurations');
      }
    } catch (err) {
      setError('Failed to save configurations');
      console.error('Error saving MCP configs:', err);
    } finally {
      setSaving(false);
    }
  };

  const addNewConfig = () => {
    const newConfig: MCPServerConfig = {
      name: '',
      description: '',
      server_type: 'stdio',
      command: '',
      args: [],
      env_vars: {},
      enabled: true,
    };
    const newIndex = configs.length;
    setConfigs([...configs, newConfig]);
    setEnvVarsInput({ ...envVarsInput, [newIndex]: '' });
  };

  const updateConfig = (index: number, field: string, value: string | boolean | string[] | Record<string, string>) => {
    const updatedConfigs = [...configs];
    updatedConfigs[index] = { ...updatedConfigs[index], [field]: value };
    setConfigs(updatedConfigs);
  };

  const deleteConfig = (index: number) => {
    const updatedConfigs = configs.filter((_, i) => i !== index);
    setConfigs(updatedConfigs);

    // Update envVarsInput by shifting indices
    const updatedEnvVarsInput: Record<number, string> = {};
    Object.entries(envVarsInput).forEach(([key, value]) => {
      const idx = parseInt(key);
      if (idx < index) {
        updatedEnvVarsInput[idx] = value;
      } else if (idx > index) {
        updatedEnvVarsInput[idx - 1] = value;
      }
      // Skip the deleted index
    });
    setEnvVarsInput(updatedEnvVarsInput);
  };

  const updateArgs = (index: number, argsString: string) => {
    const args = argsString
      .split(',')
      .map((arg) => arg.trim())
      .filter((arg) => arg);
    updateConfig(index, 'args', args);
  };

  const updateEnvVars = (index: number, envString: string) => {
    // Update the input state first
    setEnvVarsInput({ ...envVarsInput, [index]: envString });

    // Parse into key-value pairs, but be more forgiving
    const envVars: Record<string, string> = {};
    envString.split('\n').forEach((line) => {
      const trimmedLine = line.trim();
      if (trimmedLine && trimmedLine.includes('=')) {
        const [key, ...valueParts] = trimmedLine.split('=');
        const value = valueParts.join('='); // Handle values that contain '='
        if (key.trim() && value.trim()) {
          envVars[key.trim()] = value.trim();
        }
      }
    });
    updateConfig(index, 'env_vars', envVars);
  };

  if (!isOpen) return null;

  return (
    <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4'>
      <div className='bg-card rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden'>
        <div className='flex items-center justify-between p-6 border-b border-border'>
          <div className='flex items-center space-x-2'>
            <Settings className='w-5 h-5' />
            <h2 className='text-xl font-semibold'>MCP Server Configuration</h2>
          </div>
          <button onClick={onClose} className='p-2 hover:bg-secondary rounded-lg transition-colors'>
            <X className='w-5 h-5' />
          </button>
        </div>

        <div className='p-6 overflow-y-auto' style={{ maxHeight: 'calc(90vh - 160px)' }}>
          {error && (
            <div className='mb-4 p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive'>
              {error}
            </div>
          )}

          {loading ? (
            <div className='text-center py-8'>Loading configurations...</div>
          ) : (
            <div className='space-y-6'>
              {configs.map((config, index) => (
                <div key={index} className='border border-border rounded-lg p-4 space-y-4'>
                  <div className='flex items-center justify-between'>
                    <h3 className='font-medium'>MCP Server {index + 1}</h3>
                    <div className='flex items-center space-x-2'>
                      <label className='flex items-center space-x-2'>
                        <input
                          type='checkbox'
                          checked={config.enabled}
                          onChange={(e) => updateConfig(index, 'enabled', e.target.checked)}
                          className='rounded'
                        />
                        <span className='text-sm'>Enabled</span>
                      </label>
                      <button
                        onClick={() => deleteConfig(index)}
                        className='p-1 text-destructive hover:bg-destructive/10 rounded'
                      >
                        <Trash2 className='w-4 h-4' />
                      </button>
                    </div>
                  </div>

                  <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
                    <div>
                      <label className='block text-sm font-medium mb-1'>Name *</label>
                      <input
                        type='text'
                        value={config.name}
                        onChange={(e) => updateConfig(index, 'name', e.target.value)}
                        className='w-full p-2 border border-border rounded-lg bg-background'
                        placeholder='Server name'
                      />
                    </div>

                    <div>
                      <label className='block text-sm font-medium mb-1'>Type</label>
                      <select
                        value={config.server_type}
                        onChange={(e) => updateConfig(index, 'server_type', e.target.value)}
                        className='w-full p-2 border border-border rounded-lg bg-background'
                      >
                        <option value='stdio'>Standard I/O</option>
                        <option value='sse' disabled>
                          Server-Sent Events (Coming Soon)
                        </option>
                        <option value='websocket' disabled>
                          WebSocket (Coming Soon)
                        </option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className='block text-sm font-medium mb-1'>Description</label>
                    <input
                      type='text'
                      value={config.description || ''}
                      onChange={(e) => updateConfig(index, 'description', e.target.value)}
                      className='w-full p-2 border border-border rounded-lg bg-background'
                      placeholder='Brief description of the server'
                    />
                  </div>

                  {config.server_type === 'stdio' && (
                    <>
                      <div>
                        <label className='block text-sm font-medium mb-1'>Command *</label>
                        <input
                          type='text'
                          value={config.command || ''}
                          onChange={(e) => updateConfig(index, 'command', e.target.value)}
                          className='w-full p-2 border border-border rounded-lg bg-background'
                          placeholder='e.g., uvx, python, node'
                        />
                      </div>

                      <div>
                        <label className='block text-sm font-medium mb-1'>Arguments</label>
                        <input
                          type='text'
                          value={config.args?.join(', ') || ''}
                          onChange={(e) => updateArgs(index, e.target.value)}
                          className='w-full p-2 border border-border rounded-lg bg-background'
                          placeholder='Comma-separated arguments'
                        />
                        <p className='text-xs text-muted-foreground mt-1'>Example: my-mcp-server@latest, --verbose</p>
                      </div>

                      <div>
                        <label className='block text-sm font-medium mb-1'>Environment Variables</label>
                        <textarea
                          value={envVarsInput[index] || ''}
                          onChange={(e) => updateEnvVars(index, e.target.value)}
                          className='w-full p-2 border border-border rounded-lg bg-background'
                          rows={3}
                          placeholder='KEY=value&#10;ANOTHER_KEY=another_value'
                        />
                        <p className='text-xs text-muted-foreground mt-1'>One per line in KEY=value format</p>
                      </div>
                    </>
                  )}

                  {(config.server_type === 'sse' || config.server_type === 'websocket') && (
                    <div>
                      <label className='block text-sm font-medium mb-1'>URL *</label>
                      <input
                        type='url'
                        value={config.url || ''}
                        onChange={(e) => updateConfig(index, 'url', e.target.value)}
                        className='w-full p-2 border border-border rounded-lg bg-background'
                        placeholder='https://example.com/mcp'
                      />
                    </div>
                  )}
                </div>
              ))}

              <button
                onClick={addNewConfig}
                className='w-full p-4 border border-dashed border-border rounded-lg hover:bg-secondary/50 transition-colors flex items-center justify-center space-x-2'
              >
                <Plus className='w-5 h-5' />
                <span>Add MCP Server</span>
              </button>

              {/* Tools Section */}
              {showTools && (
                <div className='mt-8 border-t border-border pt-6'>
                  <div className='flex items-center justify-between mb-4'>
                    <div className='flex items-center space-x-2'>
                      <Wrench className='w-5 h-5' />
                      <h3 className='text-lg font-semibold'>Available Tools</h3>
                    </div>
                    <button
                      onClick={loadTools}
                      disabled={loadingTools}
                      className='px-3 py-1 text-sm border border-border rounded-lg hover:bg-secondary transition-colors flex items-center space-x-1 disabled:opacity-50'
                    >
                      <RefreshCw className={`w-4 h-4 ${loadingTools ? 'animate-spin' : ''}`} />
                      <span>Refresh</span>
                    </button>
                  </div>

                  {loadingTools ? (
                    <div className='text-center py-4 text-muted-foreground'>Loading tools...</div>
                  ) : tools.length > 0 ? (
                    <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3'>
                      {tools.map((tool, index) => (
                        <div key={index} className='p-3 border border-border rounded-lg bg-secondary/10'>
                          <div className='font-medium text-sm'>{tool.name}</div>
                          {tool.source && (
                            <div className='text-xs text-blue-600 dark:text-blue-400 mt-1'>{tool.source}</div>
                          )}
                          {tool.description && (
                            <div className='text-xs text-muted-foreground mt-1'>{tool.description}</div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className='text-center py-4 text-muted-foreground'>
                      No tools found. Make sure your MCP servers are configured correctly.
                    </div>
                  )}

                  {/* MCP Errors Section */}
                  {mcpErrors.length > 0 && (
                    <div className='mt-6 border-t border-border pt-4'>
                      <h4 className='text-sm font-semibold text-red-600 dark:text-red-400 mb-3 flex items-center space-x-2'>
                        <X className='w-4 h-4' />
                        <span>MCP Server Errors</span>
                      </h4>
                      <div className='space-y-2'>
                        {mcpErrors.map((error, index) => (
                          <div
                            key={index}
                            className='p-3 border border-red-200 dark:border-red-800 rounded-lg bg-red-50 dark:bg-red-950/20'
                          >
                            <div className='font-medium text-sm text-red-800 dark:text-red-200'>
                              {error.server_name}
                            </div>
                            <div className='text-xs text-red-600 dark:text-red-400 mt-1'>{error.error}</div>
                            {error.type && (
                              <div className='text-xs text-red-500 dark:text-red-500 mt-1 opacity-75'>
                                Type: {error.type}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                      <div className='mt-3 p-3 border border-yellow-200 dark:border-yellow-800 rounded-lg bg-yellow-50 dark:bg-yellow-950/20'>
                        <div className='text-xs text-yellow-800 dark:text-yellow-200'>
                          <strong>Common fixes:</strong>
                          <ul className='list-disc list-inside mt-1 space-y-1'>
                            <li>Check that the command exists (uvx, npx, python, etc.)</li>
                            <li>Verify command spelling and arguments</li>
                            <li>Ensure MCP server package is available</li>
                            <li>Check environment variables if required</li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        <div className='flex items-center justify-between p-6 border-t border-border'>
          <div className='flex items-center space-x-3'>
            {!showTools && (
              <button
                onClick={loadTools}
                disabled={loadingTools || loading}
                className='px-4 py-2 border border-border rounded-lg hover:bg-secondary transition-colors flex items-center space-x-2 disabled:opacity-50'
              >
                <Wrench className='w-4 h-4' />
                <span>{loadingTools ? 'Loading...' : 'Load Tools'}</span>
              </button>
            )}
          </div>
          <div className='flex items-center space-x-3'>
            <button
              onClick={onClose}
              className='px-4 py-2 border border-border rounded-lg hover:bg-secondary transition-colors'
            >
              {showTools ? 'Close' : 'Cancel'}
            </button>
            <button
              onClick={saveConfigs}
              disabled={saving || loading}
              className='px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors flex items-center space-x-2 disabled:opacity-50'
            >
              <Save className='w-4 h-4' />
              <span>{saving ? 'Saving...' : 'Save & Load Tools'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
