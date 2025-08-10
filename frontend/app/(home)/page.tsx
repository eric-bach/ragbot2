'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Trash2 } from 'lucide-react';
import { getCurrentUser } from 'aws-amplify/auth';
import ToolsButton from '../components/ToolsButton';
import UploadButton from '../components/UploadButton';
import TabbedResponse from '../components/TabbedResponse';
import { useTools } from '../hooks/useTools';

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  isStreaming?: boolean; // Add streaming status
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const [userId, setUserId] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { tools, loading: toolsLoading, error: toolsError } = useTools();

  // Generate session ID on component mount
  useEffect(() => {
    const getSessionId = async () => {
      try {
        const { userId } = await getCurrentUser();

        console.log('User ID:', userId);

        setUserId(userId);
        setSessionId(crypto.randomUUID());
      } catch (error) {
        console.error('Error getting user ID:', error);
      }
    };

    getSessionId();
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const clearChat = async () => {
    if (sessionId) {
      try {
        // Clear session on backend
        const albDnsName = process.env.NEXT_PUBLIC_ALB_DNS_NAME;
        if (albDnsName) {
          const response = await fetch(`https://${albDnsName}/session/${userId}/${sessionId}`, {
            method: 'DELETE',
          });

          console.log('Session cleared:', response);
        }
      } catch (error) {
        console.error('Failed to clear session on backend:', error);
      }
    }

    // Clear messages locally
    setMessages([]);

    // Generate new session ID
    const newSessionId = crypto.randomUUID();
    setSessionId(newSessionId);
    console.log('Generated new session ID after clear:', newSessionId);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue.trim(),
      role: 'user',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    // Create assistant message immediately with thinking content to show loading state
    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      content: 'RAGBot 2 is cooking...',
      role: 'assistant',
      timestamp: new Date(),
      isStreaming: true, // Mark as streaming initially
    };

    // Add the assistant message immediately to show thinking state
    setMessages((prev) => [...prev, assistantMessage]);

    try {
      console.log('Making request to /api/chat with session ID:', sessionId);

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          user_id: userId,
          query: userMessage.content,
        }),
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', Object.fromEntries(response.headers.entries()));
      console.log('Response ok:', response.ok);

      if (!response.ok) {
        // Try to get error details from the response
        let errorMessage = `HTTP error! status: ${response.status}`;
        try {
          const errorData = await response.json();
          console.error('Error response data:', errorData);
          if (errorData.details) {
            errorMessage += ` - ${errorData.details}`;
          }
          if (errorData.type) {
            errorMessage += ` (${errorData.type})`;
          }
        } catch (parseError) {
          console.error('Failed to parse error response as JSON:', parseError);
          // If parsing JSON fails, use text response
          const errorText = await response.text();
          console.error('Error response text:', errorText);
          if (errorText) {
            errorMessage += ` - ${errorText}`;
          }
        }
        throw new Error(errorMessage);
      }

      // Handle streaming response
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        console.log('Starting to read stream...');
        let accumulatedContent = '';
        let chunkCount = 0;

        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            console.log('Streaming complete, total chunks:', chunkCount);
            // Mark streaming as complete
            setMessages((prev) => prev.map((msg) => (msg.id === assistantMessage.id ? { ...msg, isStreaming: false } : msg)));
            break;
          }

          if (value) {
            chunkCount++;
            const chunk = decoder.decode(value, { stream: true });
            console.log(`Chunk ${chunkCount}:`, chunk.substring(0, 100));
            accumulatedContent += chunk;

            // Update the assistant message content in real-time
            setMessages((prev) => prev.map((msg) => (msg.id === assistantMessage.id ? { ...msg, content: accumulatedContent, isStreaming: true } : msg)));
          }
        }
      } else {
        console.log('No reader available');
      }
    } catch (error) {
      console.error('Error calling RAGBot API:', error);

      let errorContent = 'Sorry, I encountered an error while processing your request. Please try again.';

      // If it's a response error, try to get more details
      if (error instanceof Error) {
        console.error('Error details:', error.message);
        errorContent += `\n\nError details: ${error.message}`;
      }

      // Update the existing assistant message with error content
      setMessages((prev) => prev.map((msg) => (msg.id === assistantMessage.id ? { ...msg, content: errorContent, isStreaming: false } : msg)));
    } finally {
      setIsLoading(false);
    }
  };

  // Show error state if tools failed to load
  if (toolsError) {
    return (
      <div className='flex flex-col h-full max-w-4xl mx-auto'>
        <div className='flex-1 overflow-y-auto px-4 py-4'>
          <div className='flex items-center justify-center h-full'>
            <div className='text-center text-red-600'>
              <h2 className='text-xl font-semibold mb-2'>Failed to Initialize</h2>
              <p className='mb-4'>Unable to load tools. Please refresh the page.</p>
              <p className='text-sm text-muted-foreground'>Error: {toolsError}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className='flex flex-col h-full max-w-4xl mx-auto'>
      {/* Messages Area */}
      <div className='flex-1 overflow-y-auto px-4 py-4 space-y-4'>
        {messages.length === 0 && (
          <div className='flex items-center justify-center h-full'>
            <div className='text-center text-muted-foreground'>
              <h2 className='text-2xl font-semibold mb-2'>Welcome to RAGBot 2</h2>
              <p>Start a conversation by typing a message below.</p>
              {toolsLoading ? (
                <p className='text-sm mt-2 text-muted-foreground'>Loading tools in background...</p>
              ) : (
                <p className='text-sm mt-2'>Tools loaded: {tools.length} available</p>
              )}
              {sessionId && <p className='text-xs mt-1 text-muted-foreground'>Session: {sessionId.substring(0, 8)}...</p>}
              <p className='text-xs mt-1 text-muted-foreground'>Memory: Last 10 message pairs</p>
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-sm md:max-w-lg lg:max-w-xl xl:max-w-2xl px-4 py-2 rounded-lg ${
                message.role === 'user' ? 'bg-primary text-primary-foreground ml-auto' : 'bg-muted text-muted-foreground'
              }`}
            >
              {message.role === 'user' ? (
                <div>
                  <p className='whitespace-pre-wrap break-words text-sm'>{message.content}</p>
                  <p className='text-xs opacity-70 mt-1'>{message.timestamp.toLocaleTimeString()}</p>
                </div>
              ) : message.isStreaming ? (
                <div>
                  <p className='whitespace-pre-wrap break-words text-sm'>{message.content}</p>
                  <p className='text-xs opacity-70 mt-1'>{message.timestamp.toLocaleTimeString()}</p>
                </div>
              ) : (
                <TabbedResponse key={message.id} content={message.content} />
              )}
            </div>
          </div>
        ))}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className='flex-shrink-0 border-t border-border p-4'>
        <form onSubmit={handleSubmit} className='max-w-4xl mx-auto'>
          <div className='border border-input rounded-lg bg-background'>
            {/* Text Input Row */}
            <div className='relative'>
              <input
                type='text'
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder='Type your message...'
                disabled={isLoading}
                className='w-full px-4 py-3 border-0 bg-transparent text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-0 disabled:opacity-50 disabled:cursor-not-allowed'
              />
            </div>

            {/* Buttons Row */}
            <div className='flex items-center justify-between px-3 py-2'>
              <div className='flex items-center space-x-2'>
                <UploadButton userId={userId} />
                <ToolsButton tools={tools} loading={toolsLoading} error={toolsError} />
              </div>
              <div className='flex items-center space-x-2'>
                {messages.length > 0 && (
                  <button
                    type='button'
                    onClick={clearChat}
                    disabled={isLoading}
                    className='flex items-center space-x-1 text-muted-foreground hover:text-foreground transition-colors'
                    title='Start a new chat'
                  >
                    <Trash2 size={14} />
                    <span className='text-xs'>Clear Chat</span>
                  </button>
                )}
                <button
                  type='submit'
                  disabled={!inputValue.trim() || isLoading}
                  className='w-8 h-8 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center'
                >
                  <Send size={16} />
                </button>
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
