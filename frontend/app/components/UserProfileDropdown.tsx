'use client';

import React, { useState, useRef, useEffect } from 'react';
import { User, LogOut, Settings } from 'lucide-react';
import { AuthUser } from 'aws-amplify/auth';
import { AuthEventData } from '@aws-amplify/ui';
import MCPConfigButton from './MCPConfigButton';

interface UserProfileDropdownProps {
  user: AuthUser;
  signOut: (data?: AuthEventData | undefined) => void;
}

export default function UserProfileDropdown({ user, signOut }: UserProfileDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [showMCPConfig, setShowMCPConfig] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const userName = user.signInDetails?.loginId || user.username || 'User';
  const userId = user.userId || user.username || '';

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleSignOut = () => {
    signOut();
    setIsOpen(false);
  };

  const handleMCPConfig = () => {
    setShowMCPConfig(true);
    setIsOpen(false);
  };

  return (
    <>
      <div className='relative' ref={dropdownRef}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className='flex items-center justify-center w-8 h-8 bg-primary rounded-full hover:bg-primary/80 transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2'
        >
          <User className='w-4 h-4 text-primary-foreground' />
        </button>

        {isOpen && (
          <div className='absolute right-0 mt-2 w-48 bg-card border border-border rounded-md shadow-lg z-50'>
            <div className='py-1'>
              <div className='px-4 py-2 text-sm text-muted-foreground border-b border-border'>
                <div className='font-medium text-foreground'>{userName}</div>
                <div className='text-xs'>Signed in</div>
              </div>
              <button
                onClick={handleMCPConfig}
                className='w-full flex items-center space-x-2 px-4 py-2 text-sm text-foreground hover:bg-secondary transition-colors'
              >
                <Settings className='w-4 h-4' />
                <div className='text-sm'>MCP Servers</div>
              </button>
              <button
                onClick={handleSignOut}
                className='w-full flex items-center space-x-2 px-4 py-2 text-sm text-foreground hover:bg-secondary transition-colors'
              >
                <LogOut className='w-4 h-4' />
                <div className='text-sm'>Sign Out</div>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* MCP Config Modal */}
      {showMCPConfig && (
        <MCPConfigButton userId={userId} onClose={() => setShowMCPConfig(false)} showAsButton={false} />
      )}
    </>
  );
}
