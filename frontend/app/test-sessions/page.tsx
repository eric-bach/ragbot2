'use client';

import { useState } from 'react';
import { useSessions } from '../hooks/useSessions';

export default function SessionTestPage() {
  const [userId, setUserId] = useState('test-user-123');
  const [sessionTitle, setSessionTitle] = useState('');
  const [newTitle, setNewTitle] = useState('');
  const [selectedSessionId, setSelectedSessionId] = useState('');

  const {
    sessions,
    currentSession,
    loading,
    error,
    createSession,
    loadSessions,
    loadSession,
    updateSessionTitle,
    deleteSession,
    clearError,
  } = useSessions(userId);

  const handleCreateSession = async () => {
    const session = await createSession(sessionTitle || undefined);
    if (session) {
      setSessionTitle('');
      console.log('Created session:', session);
    }
  };

  const handleLoadSession = async () => {
    if (selectedSessionId) {
      const session = await loadSession(selectedSessionId);
      console.log('Loaded session:', session);
    }
  };

  const handleUpdateTitle = async () => {
    if (selectedSessionId && newTitle) {
      const success = await updateSessionTitle(selectedSessionId, newTitle);
      if (success) {
        setNewTitle('');
        console.log('Updated session title');
      }
    }
  };

  const handleDeleteSession = async () => {
    if (selectedSessionId) {
      const success = await deleteSession(selectedSessionId);
      if (success) {
        setSelectedSessionId('');
        console.log('Deleted session');
      }
    }
  };

  return (
    <div className='p-8 max-w-4xl mx-auto'>
      <h1 className='text-3xl font-bold mb-8'>Session Management Test</h1>

      {error && (
        <div className='bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4'>
          <strong>Error:</strong> {error}
          <button onClick={clearError} className='ml-2 text-red-900 underline'>
            Clear
          </button>
        </div>
      )}

      <div className='grid grid-cols-1 md:grid-cols-2 gap-8'>
        {/* Left Column - Controls */}
        <div className='space-y-6'>
          <div>
            <label className='block text-sm font-medium mb-2'>User ID:</label>
            <input
              type='text'
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              className='w-full p-2 border border-gray-300 rounded'
              placeholder='Enter user ID'
            />
          </div>

          <div>
            <h3 className='text-lg font-semibold mb-2'>Create Session</h3>
            <input
              type='text'
              value={sessionTitle}
              onChange={(e) => setSessionTitle(e.target.value)}
              className='w-full p-2 border border-gray-300 rounded mb-2'
              placeholder='Session title (optional)'
            />
            <button
              onClick={handleCreateSession}
              disabled={loading}
              className='w-full bg-blue-500 text-white p-2 rounded hover:bg-blue-600 disabled:opacity-50'
            >
              {loading ? 'Creating...' : 'Create Session'}
            </button>
          </div>

          <div>
            <h3 className='text-lg font-semibold mb-2'>Session Operations</h3>
            <select
              value={selectedSessionId}
              onChange={(e) => setSelectedSessionId(e.target.value)}
              className='w-full p-2 border border-gray-300 rounded mb-2'
            >
              <option value=''>Select a session</option>
              {sessions.map((session) => (
                <option key={session.session_id} value={session.session_id}>
                  {session.title} ({session.session_id.slice(-8)})
                </option>
              ))}
            </select>

            <div className='space-y-2'>
              <button
                onClick={handleLoadSession}
                disabled={!selectedSessionId || loading}
                className='w-full bg-green-500 text-white p-2 rounded hover:bg-green-600 disabled:opacity-50'
              >
                Load Session Details
              </button>

              <input
                type='text'
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                className='w-full p-2 border border-gray-300 rounded'
                placeholder='New title'
              />
              <button
                onClick={handleUpdateTitle}
                disabled={!selectedSessionId || !newTitle || loading}
                className='w-full bg-yellow-500 text-white p-2 rounded hover:bg-yellow-600 disabled:opacity-50'
              >
                Update Title
              </button>

              <button
                onClick={handleDeleteSession}
                disabled={!selectedSessionId || loading}
                className='w-full bg-red-500 text-white p-2 rounded hover:bg-red-600 disabled:opacity-50'
              >
                Delete Session
              </button>
            </div>
          </div>

          <button
            onClick={loadSessions}
            disabled={loading}
            className='w-full bg-gray-500 text-white p-2 rounded hover:bg-gray-600 disabled:opacity-50'
          >
            {loading ? 'Loading...' : 'Refresh Sessions'}
          </button>
        </div>

        {/* Right Column - Data Display */}
        <div className='space-y-6'>
          <div>
            <h3 className='text-lg font-semibold mb-2'>Sessions ({sessions.length})</h3>
            <div className='bg-gray-50 p-4 rounded max-h-60 overflow-y-auto'>
              {sessions.length === 0 ? (
                <p className='text-gray-500'>No sessions found</p>
              ) : (
                <div className='space-y-2'>
                  {sessions.map((session) => (
                    <div key={session.session_id} className='bg-white p-2 rounded border text-sm'>
                      <div className='font-medium'>{session.title}</div>
                      <div className='text-gray-500'>ID: {session.session_id.slice(-8)}...</div>
                      <div className='text-gray-500'>
                        Messages: {session.message_count} | Updated: {new Date(session.updated_at).toLocaleString()}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div>
            <h3 className='text-lg font-semibold mb-2'>Current Session Details</h3>
            <div className='bg-gray-50 p-4 rounded max-h-60 overflow-y-auto'>
              {currentSession ? (
                <div className='text-sm'>
                  <div>
                    <strong>Title:</strong> {currentSession.title}
                  </div>
                  <div>
                    <strong>ID:</strong> {currentSession.session_id}
                  </div>
                  <div>
                    <strong>Messages:</strong> {currentSession.messages.length}
                  </div>
                  <div>
                    <strong>Created:</strong> {new Date(currentSession.created_at).toLocaleString()}
                  </div>
                  <div>
                    <strong>Updated:</strong> {new Date(currentSession.updated_at).toLocaleString()}
                  </div>
                  {currentSession.messages.length > 0 && (
                    <div className='mt-2'>
                      <strong>Messages:</strong>
                      <pre className='bg-white p-2 mt-1 rounded border text-xs'>
                        {JSON.stringify(currentSession.messages, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              ) : (
                <p className='text-gray-500'>No session loaded</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
