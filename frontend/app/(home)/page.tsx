'use client';

import { useState, useRef, useEffect } from 'react';

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

    // Simulate AI response (replace with actual API call later)
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `I received your message: "${userMessage.content}". This is a placeholder response. The actual RAGBot functionality will be implemented later.`,
        role: 'assistant',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 1000);
  };

  return (
    <div className='flex flex-col h-full max-w-4xl mx-auto'>
      {/* Messages Area */}
      <div className='flex-1 overflow-y-auto px-4 py-4 space-y-4'>
        {messages.length === 0 && (
          <div className='flex items-center justify-center h-full'>
            <div className='text-center text-muted-foreground'>
              <h2 className='text-2xl font-semibold mb-2'>Welcome to RAGBot</h2>
              <p>Start a conversation by typing a message below.</p>
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-xs md:max-w-md lg:max-w-lg xl:max-w-xl px-4 py-2 rounded-lg ${
                message.role === 'user'
                  ? 'bg-primary text-primary-foreground ml-auto'
                  : 'bg-muted text-muted-foreground'
              }`}
            >
              <p className='whitespace-pre-wrap break-words'>{message.content}</p>
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
                <span className='text-sm'>RAGBot is thinking...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className='flex-shrink-0 border-t border-border p-4'>
        <form onSubmit={handleSubmit} className='flex space-x-2'>
          <input
            type='text'
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder='Type your message...'
            disabled={isLoading}
            className='flex-1 px-4 py-2 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed'
          />
          <button
            type='submit'
            disabled={!inputValue.trim() || isLoading}
            className='px-6 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors'
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
