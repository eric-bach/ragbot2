'use client';

import { useState, useRef, useEffect } from 'react';
import ToolsButton from '../components/ToolsButton';
import TabbedResponse from '../components/TabbedResponse';

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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

    try {
      console.log('Making request to /api/chat...');
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
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
          if (errorData.details) {
            errorMessage += ` - ${errorData.details}`;
          }
          if (errorData.type) {
            errorMessage += ` (${errorData.type})`;
          }
        } catch {
          // If parsing JSON fails, use text response
          const errorText = await response.text();
          if (errorText) {
            errorMessage += ` - ${errorText}`;
          }
        }
        throw new Error(errorMessage);
      }

      // Create assistant message with empty content that will be updated as chunks arrive
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: '',
        role: 'assistant',
        timestamp: new Date(),
      };

      // Add the empty message to state first
      setMessages((prev) => [...prev, assistantMessage]);

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
            break;
          }

          if (value) {
            chunkCount++;
            const chunk = decoder.decode(value, { stream: true });
            console.log(`Chunk ${chunkCount}:`, chunk.substring(0, 100));
            accumulatedContent += chunk;

            // Update the assistant message content in real-time
            setMessages((prev) =>
              prev.map((msg) => (msg.id === assistantMessage.id ? { ...msg, content: accumulatedContent } : msg))
            );
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

      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: errorContent,
        role: 'assistant',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className='flex flex-col h-full max-w-4xl mx-auto'>
      {/* Messages Area */}
      <div className='flex-1 overflow-y-auto px-4 py-4 space-y-4'>
        {messages.length === 0 && (
          <div className='flex items-center justify-center h-full'>
            <div className='text-center text-muted-foreground'>
              <h2 className='text-2xl font-semibold mb-2'>Welcome to RAGBot 2</h2>
              <p>Start a conversation by typing a message below.</p>
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-sm md:max-w-lg lg:max-w-xl xl:max-w-2xl px-4 py-2 rounded-lg ${
                message.role === 'user'
                  ? 'bg-primary text-primary-foreground ml-auto'
                  : 'bg-muted text-muted-foreground'
              }`}
            >
              {message.role === 'user' ? (
                <p className='whitespace-pre-wrap break-words text-sm'>{message.content}</p>
              ) : (
                <TabbedResponse content={message.content} />
              )}
              <p className='text-xs opacity-70 mt-1'>{message.timestamp.toLocaleTimeString()}</p>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className='flex justify-start'>
            <div className='bg-muted text-muted-foreground px-4 py-2 rounded-lg'>
              <div className='flex items-center space-x-2'>
                <div className='flex space-x-1'>
                  <div className='w-2 h-2 bg-current rounded-full animate-bounce [animation-delay:-0.3s]'></div>
                  <div className='w-2 h-2 bg-current rounded-full animate-bounce [animation-delay:-0.15s]'></div>
                  <div className='w-2 h-2 bg-current rounded-full animate-bounce'></div>
                </div>
                <span className='text-sm'>RAGBot 2 is thinking...</span>
              </div>
            </div>
          </div>
        )}

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
              <ToolsButton />
              <button
                type='submit'
                disabled={!inputValue.trim() || isLoading}
                className='w-8 h-8 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center'
              >
                <svg
                  width='16'
                  height='16'
                  viewBox='0 0 24 24'
                  fill='none'
                  stroke='currentColor'
                  strokeWidth='2'
                  strokeLinecap='round'
                  strokeLinejoin='round'
                >
                  <path d='m22 2-7 20-4-9-9-4 20-7z' />
                  <path d='M22 2 11 13' />
                </svg>
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
