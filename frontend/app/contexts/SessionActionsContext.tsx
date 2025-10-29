'use client';

import React, { createContext, useContext } from 'react';
import { Session } from '../hooks/useSessions';

interface SessionActionsContextType {
  addSessionToList: (session: Session) => void;
  updateSessionMessageCount: (sessionId: string, messageCount: number) => void;
  createSession: (title?: string) => Promise<Session | null>;
  refreshSession: (sessionId: string) => Promise<void>;
}

const SessionActionsContext = createContext<SessionActionsContextType | undefined>(undefined);

export function useSessionActions() {
  const context = useContext(SessionActionsContext);
  if (context === undefined) {
    throw new Error('useSessionActions must be used within a SessionActionsProvider');
  }
  return context;
}

interface SessionActionsProviderProps {
  children: React.ReactNode;
  addSessionToList: (session: Session) => void;
  updateSessionMessageCount: (sessionId: string, messageCount: number) => void;
  createSession: (title?: string) => Promise<Session | null>;
  refreshSession: (sessionId: string) => Promise<void>;
}

export function SessionActionsProvider({
  children,
  addSessionToList,
  updateSessionMessageCount,
  createSession,
  refreshSession,
}: SessionActionsProviderProps) {
  return (
    <SessionActionsContext.Provider
      value={{ addSessionToList, updateSessionMessageCount, createSession, refreshSession }}
    >
      {children}
    </SessionActionsContext.Provider>
  );
}
