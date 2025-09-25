'use client';

import React, { useState } from 'react';
import { Plus, Edit2, Trash2, X, Check, ChevronLeft, MessageCircle } from 'lucide-react';
import { Session } from '../hooks/useSessions';

interface SessionSidebarProps {
  userId: string;
  currentSessionId: string | null;
  onSessionSelect: (sessionId: string) => void;
  onNewSession: () => void;
  isOpen: boolean;
  onToggle: () => void;
  className?: string;
  sessions: Session[];
  loading: boolean;
  error: string | null;
  createSession: (title?: string) => Promise<Session | null>;
  updateSessionTitle: (sessionId: string, title: string) => Promise<boolean>;
  deleteSession: (sessionId: string) => Promise<boolean>;
  clearError: () => void;
}

interface SessionItemProps {
  session: Session;
  isActive: boolean;
  onSelect: () => void;
  onDelete: () => void;
  onTitleUpdate: (newTitle: string) => void;
}

function SessionItem({ session, isActive, onSelect, onDelete, onTitleUpdate }: SessionItemProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(session.title);

  const handleStartEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditTitle(session.title);
    setIsEditing(true);
  };

  const handleSaveEdit = () => {
    if (editTitle.trim() && editTitle.trim() !== session.title) {
      onTitleUpdate(editTitle.trim());
    }
    setIsEditing(false);
  };

  const handleCancelEdit = () => {
    setEditTitle(session.title);
    setIsEditing(false);
  };

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSaveEdit();
    } else if (e.key === 'Escape') {
      handleCancelEdit();
    }
  };

  const formatDate = (dateString: string) => {
    if (!dateString) {
      console.warn('formatDate called with empty dateString');
      return 'Just now';
    }

    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      console.warn('formatDate called with invalid dateString:', dateString);
      return 'Just now';
    }

    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return `${diffDays} days ago`;
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
  };

  return (
    <div
      onClick={onSelect}
      className={`group relative p-3 rounded-lg cursor-pointer transition-all duration-150 ${
        isActive ? 'bg-blue-50 border-l-4 border-blue-500 shadow-sm' : 'hover:bg-gray-50 border-l-4 border-transparent'
      }`}
    >
      <div className='flex items-start justify-between gap-2'>
        <div className='flex-1 min-w-0'>
          {isEditing ? (
            <div className='flex items-center gap-1'>
              <input
                type='text'
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                onKeyDown={handleKeyDown}
                onBlur={handleSaveEdit}
                className='flex-1 text-sm font-medium bg-white border border-gray-200 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500'
                autoFocus
                onClick={(e) => e.stopPropagation()}
              />
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleSaveEdit();
                }}
                className='p-1 text-green-600 hover:bg-green-100 rounded'
              >
                <Check size={14} />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleCancelEdit();
                }}
                className='p-1 text-gray-400 hover:bg-gray-100 rounded'
              >
                <X size={14} />
              </button>
            </div>
          ) : (
            <>
              <h3 className='text-sm font-medium text-gray-900 truncate pr-2'>{session.title}</h3>
              <div className='flex items-center gap-2 mt-1 text-xs text-gray-500'>
                <span>{formatDate(session.updated_at)}</span>
              </div>
            </>
          )}
        </div>

        {!isEditing && (
          <div className='flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity'>
            <button
              onClick={handleStartEdit}
              className='p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded'
              title='Edit title'
            >
              <Edit2 size={14} />
            </button>
            <button
              onClick={handleDelete}
              className='p-1 rounded transition-colors text-gray-400 hover:text-red-600 hover:bg-red-100'
              title='Delete session'
            >
              <Trash2 size={14} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default function SessionSidebar({
  userId,
  currentSessionId,
  onSessionSelect,
  onNewSession,
  isOpen,
  onToggle,
  className = '',
  sessions,
  loading,
  error,
  createSession,
  updateSessionTitle,
  deleteSession,
  clearError,
}: SessionSidebarProps) {
  const [isCreating, setIsCreating] = useState(false);

  const handleNewSession = async () => {
    setIsCreating(true);
    try {
      const newSession = await createSession();
      if (newSession) {
        onNewSession();
        onSessionSelect(newSession.session_id);
      }
    } finally {
      setIsCreating(false);
    }
  };

  const handleSessionSelect = (sessionId: string) => {
    onSessionSelect(sessionId);
    // Close sidebar on mobile after selection
    if (window.innerWidth < 768) {
      onToggle();
    }
  };

  const handleTitleUpdate = async (sessionId: string, newTitle: string) => {
    await updateSessionTitle(sessionId, newTitle);
  };

  const handleDeleteSession = async (sessionId: string) => {
    console.log('Deleting session:', sessionId);

    try {
      await deleteSession(sessionId);
      if (currentSessionId === sessionId) {
        // If we deleted the current session, clear the current session without creating a new one
        onSessionSelect('');
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  // Group sessions by date
  const groupedSessions = React.useMemo(() => {
    const groups: { [key: string]: Session[] } = {
      Today: [],
      Yesterday: [],
      'Last 7 days': [],
      'Last 30 days': [],
      Older: [],
    };

    const now = new Date();
    sessions.forEach((session) => {
      const sessionDate = new Date(session.updated_at);
      const diffMs = now.getTime() - sessionDate.getTime();
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

      if (diffDays === 0 || isNaN(sessionDate.getTime())) {
        groups.Today.push(session);
      } else if (diffDays === 1) {
        groups.Yesterday.push(session);
      } else if (diffDays < 7) {
        groups['Last 7 days'].push(session);
      } else if (diffDays < 30) {
        groups['Last 30 days'].push(session);
      } else {
        groups.Older.push(session);
      }
    });

    // Sort sessions within each group - "Just now" sessions (invalid dates) first, then by time
    Object.keys(groups).forEach((groupName) => {
      groups[groupName].sort((a, b) => {
        const dateA = new Date(a.updated_at);
        const dateB = new Date(b.updated_at);
        const isInvalidA = isNaN(dateA.getTime());
        const isInvalidB = isNaN(dateB.getTime());

        // Invalid dates (which show as "Just now") should come first
        if (isInvalidA && !isInvalidB) return -1;
        if (!isInvalidA && isInvalidB) return 1;
        if (isInvalidA && isInvalidB) return 0;

        // For valid dates, sort by most recent first
        return dateB.getTime() - dateA.getTime();
      });
    });

    return groups;
  }, [sessions]);

  return (
    <>
      {/* Sidebar */}
      <div
        className={`flex-shrink-0 bg-white border-r border-gray-200 flex flex-col transition-all duration-200 ease-in-out overflow-hidden ${
          isOpen ? 'w-80' : 'w-0'
        } ${className}`}
      >
        {/* Header */}
        <div
          className={`flex items-center justify-between p-4 border-b border-gray-200 ${
            isOpen ? 'opacity-100' : 'opacity-0'
          } transition-opacity duration-200`}
        >
          <h2 className='text-lg font-semibold text-gray-900'>
            Chat History{' '}
            {sessions.length > 0 && <span className='text-md font-normal text-gray-700'>({sessions.length})</span>}
          </h2>
          <div className='flex items-center gap-2'>
            <button
              onClick={handleNewSession}
              disabled={isCreating || loading}
              className='p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50'
              title='New chat'
            >
              <Plus size={20} />
            </button>
            <button
              onClick={onToggle}
              className='p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg'
              title='Toggle sidebar'
            >
              <ChevronLeft size={20} />
            </button>
          </div>
        </div>

        {/* Error display */}
        {error && (
          <div
            className={`mx-4 mt-4 p-3 bg-red-50 border border-red-200 rounded-lg ${
              isOpen ? 'opacity-100' : 'opacity-0'
            } transition-opacity duration-200`}
          >
            <div className='flex items-center justify-between'>
              <p className='text-sm text-red-600'>{error}</p>
              <button onClick={clearError} className='text-red-400 hover:text-red-600'>
                <X size={16} />
              </button>
            </div>
          </div>
        )}

        {/* Session list */}
        <div
          className={`flex-1 overflow-y-auto ${isOpen ? 'opacity-100' : 'opacity-0'} transition-opacity duration-200`}
        >
          {loading && sessions.length === 0 ? (
            <div className='flex items-center justify-center h-32'>
              <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500'></div>
            </div>
          ) : sessions.length === 0 ? (
            <div className='flex flex-col items-center justify-center h-32 text-gray-500'>
              <MessageCircle size={32} className='mb-2' />
              <p className='text-sm'>No chat history yet</p>
              <p className='text-xs'>Start a conversation to see your sessions</p>
            </div>
          ) : (
            <div className='p-4 space-y-6'>
              {Object.entries(groupedSessions).map(([groupName, groupSessions]) => {
                if (groupSessions.length === 0) return null;

                return (
                  <div key={groupName}>
                    <h3 className='text-xs font-medium text-gray-500 uppercase tracking-wider mb-2'>{groupName}</h3>
                    <div className='space-y-1'>
                      {groupSessions.map((session) => (
                        <SessionItem
                          key={session.session_id}
                          session={session}
                          isActive={session.session_id === currentSessionId}
                          onSelect={() => handleSessionSelect(session.session_id)}
                          onDelete={() => handleDeleteSession(session.session_id)}
                          onTitleUpdate={(newTitle) => handleTitleUpdate(session.session_id, newTitle)}
                        />
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          className={`p-4 border-t border-gray-200 text-xs text-gray-500 ${
            isOpen ? 'opacity-100' : 'opacity-0'
          } transition-opacity duration-200`}
        >
          {sessions.length > 0 && (
            <p>
              {sessions.length} conversation{sessions.length !== 1 ? 's' : ''}
            </p>
          )}
        </div>
      </div>
    </>
  );
}
