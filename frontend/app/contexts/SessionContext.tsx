'use client';

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

interface SessionContextType {
  currentSessionId: string | null;
  setCurrentSessionId: (sessionId: string | null) => void;
  createNewSession: () => void;
  loadSession: (sessionId: string) => void;
  ensureSession: () => string; // Creates session if none exists and returns session ID
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

export function useSessionContext() {
  const context = useContext(SessionContext);
  if (context === undefined) {
    throw new Error('useSessionContext must be used within a SessionProvider');
  }
  return context;
}

interface SessionProviderProps {
  children: ReactNode;
}

export function SessionProvider({ children }: SessionProviderProps) {
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  const createNewSession = useCallback(() => {
    const newSessionId = crypto.randomUUID();
    setCurrentSessionId(newSessionId);
    console.log('Created new session:', newSessionId);
  }, []);

  const loadSession = useCallback((sessionId: string) => {
    setCurrentSessionId(sessionId || null);
    console.log('Loaded session:', sessionId || 'cleared');
  }, []);

  const ensureSession = useCallback(() => {
    if (currentSessionId) {
      return currentSessionId;
    }

    const newSessionId = crypto.randomUUID();
    setCurrentSessionId(newSessionId);
    console.log('Created new session on demand:', newSessionId);
    return newSessionId;
  }, [currentSessionId]);

  const value: SessionContextType = {
    currentSessionId,
    setCurrentSessionId,
    createNewSession,
    loadSession,
    ensureSession,
  };

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}
