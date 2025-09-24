import { useState, useCallback, useEffect } from 'react';

export interface SessionMessage {
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
}

export interface Session {
  session_id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface SessionWithHistory extends Session {
  messages: SessionMessage[];
}

export interface CreateSessionRequest {
  title?: string;
}

export interface UseSessions {
  sessions: Session[];
  currentSession: SessionWithHistory | null;
  loading: boolean;
  error: string | null;
  createSession: (title?: string) => Promise<Session | null>;
  loadSessions: () => Promise<void>;
  loadSession: (sessionId: string) => Promise<SessionWithHistory | null>;
  updateSessionTitle: (sessionId: string, title: string) => Promise<boolean>;
  deleteSession: (sessionId: string) => Promise<boolean>;
  clearError: () => void;
}

export function useSessions(userId: string): UseSessions {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSession, setCurrentSession] = useState<SessionWithHistory | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const loadSessions = useCallback(async () => {
    if (!userId) return;

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/sessions/${userId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to load sessions');
      }

      const data = await response.json();
      setSessions(data.sessions || []);
    } catch (err) {
      console.error('Error loading sessions:', err);
      setError(err instanceof Error ? err.message : 'Failed to load sessions');
    } finally {
      setLoading(false);
    }
  }, [userId]);

  const createSession = useCallback(
    async (title?: string): Promise<Session | null> => {
      if (!userId) return null;

      try {
        setLoading(true);
        setError(null);

        const response = await fetch(`/api/sessions/${userId}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            title: title || 'New Chat',
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Failed to create session');
        }

        const newSession = await response.json();

        // Add the new session to the list and sort by updated_at (most recent first)
        setSessions((prevSessions) => {
          const updatedSessions = [newSession, ...prevSessions];
          return updatedSessions.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
        });

        return newSession;
      } catch (err) {
        console.error('Error creating session:', err);
        setError(err instanceof Error ? err.message : 'Failed to create session');
        return null;
      } finally {
        setLoading(false);
      }
    },
    [userId]
  );

  const loadSession = useCallback(
    async (sessionId: string): Promise<SessionWithHistory | null> => {
      if (!userId || !sessionId) return null;

      try {
        setLoading(true);
        setError(null);

        const response = await fetch(`/api/sessions/${userId}/${sessionId}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Failed to load session');
        }

        const sessionData = await response.json();
        setCurrentSession(sessionData);
        return sessionData;
      } catch (err) {
        console.error('Error loading session:', err);
        setError(err instanceof Error ? err.message : 'Failed to load session');
        return null;
      } finally {
        setLoading(false);
      }
    },
    [userId]
  );

  const updateSessionTitle = useCallback(
    async (sessionId: string, title: string): Promise<boolean> => {
      if (!userId || !sessionId || !title.trim()) return false;

      try {
        setError(null);

        const response = await fetch(`/api/sessions/${userId}/${sessionId}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            title: title.trim(),
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Failed to update session title');
        }

        // Update the session in the list
        setSessions((prevSessions) =>
          prevSessions.map((session) =>
            session.session_id === sessionId
              ? { ...session, title: title.trim(), updated_at: new Date().toISOString() }
              : session
          )
        );

        // Update current session if it matches
        if (currentSession && currentSession.session_id === sessionId) {
          setCurrentSession((prev) =>
            prev ? { ...prev, title: title.trim(), updated_at: new Date().toISOString() } : null
          );
        }

        return true;
      } catch (err) {
        console.error('Error updating session title:', err);
        setError(err instanceof Error ? err.message : 'Failed to update session title');
        return false;
      }
    },
    [userId, currentSession]
  );

  const deleteSession = useCallback(
    async (sessionId: string): Promise<boolean> => {
      if (!userId || !sessionId) return false;

      try {
        setError(null);

        const response = await fetch(`/api/sessions/${userId}/${sessionId}`, {
          method: 'DELETE',
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Failed to delete session');
        }

        // Remove the session from the list
        setSessions((prevSessions) => prevSessions.filter((session) => session.session_id !== sessionId));

        // Clear current session if it was deleted
        if (currentSession && currentSession.session_id === sessionId) {
          setCurrentSession(null);
        }

        return true;
      } catch (err) {
        console.error('Error deleting session:', err);
        setError(err instanceof Error ? err.message : 'Failed to delete session');
        return false;
      }
    },
    [userId, currentSession]
  );

  // Load sessions when userId changes
  useEffect(() => {
    if (userId) {
      loadSessions();
    }
  }, [userId, loadSessions]);

  return {
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
  };
}
