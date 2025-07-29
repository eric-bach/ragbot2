'use client';

import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface TabbedResponseProps {
  content: string;
}

type TabType = 'answer' | 'sources' | 'steps';

export default function TabbedResponse({ content }: TabbedResponseProps) {
  // Extract thinking content (steps)
  const thinkingMatch = content.match(/<thinking>([\s\S]*?)<\/thinking>/);
  const thinkingContent = thinkingMatch ? thinkingMatch[1].trim() : '';

  // Extract sources content
  const sourcesMatch = content.match(/<sources>([\s\S]*?)<\/sources>/);
  const rawSourcesContent = sourcesMatch ? sourcesMatch[1].trim() : '';

  // Parse and format sources if they exist
  const formatSources = (rawContent: string) => {
    if (!rawContent) return '';

    // Extract individual source elements - handle both self-closing and nested tags
    const sourceMatches = rawContent.match(/<source[^>]*\/?>([\s\S]*?)<\/source>|<source[^>]*\/?>/g);
    if (!sourceMatches) return rawContent; // Return raw content if no source tags found

    const formattedSources = sourceMatches.map((sourceTag, index) => {
      // Try to extract attributes from self-closing tags first
      const nameMatch = sourceTag.match(/name="([^"]*)"/);
      const urlMatch = sourceTag.match(/url="([^"]*)"/);
      const snippetMatch = sourceTag.match(/snippet="([^"]*)"/);

      const name = nameMatch ? nameMatch[1].trim() : '';
      const url = urlMatch ? urlMatch[1].trim() : '';
      const snippet = snippetMatch ? snippetMatch[1].trim() : '';

      // If we have name and url from attributes, use them
      if (name && url) {
        let formattedSource = `${index + 1}. **[${name}](${url})**`;
        if (snippet) {
          formattedSource += `\n\n   ${snippet}`;
        }
        return formattedSource;
      }

      // Fallback: try to extract nested tags
      const nestedUrlMatch = sourceTag.match(/<url>([\s\S]*?)<\/url>/);
      const nestedTitleMatch = sourceTag.match(/<title>([\s\S]*?)<\/title>/);

      const nestedUrl = nestedUrlMatch ? nestedUrlMatch[1].trim() : '';
      const nestedTitle = nestedTitleMatch ? nestedTitleMatch[1].trim() : '';

      if (nestedUrl && nestedTitle) {
        return `${index + 1}. [${nestedTitle}](${nestedUrl})`;
      } else if (nestedUrl) {
        return `${index + 1}. [${nestedUrl}](${nestedUrl})`;
      } else {
        return `${index + 1}. ${sourceTag.replace(/<[^>]*>/g, '').trim()}`;
      }
    });

    return formattedSources.join('\n\n');
  };

  const sourcesContent = formatSources(rawSourcesContent);

  // Get answer content (everything except thinking and sources tags)
  const answerContent = content
    .replace(/<thinking>[\s\S]*?<\/thinking>/g, '')
    .replace(/<sources>[\s\S]*?<\/sources>/g, '')
    .trim();

  const tabs = [
    {
      id: 'answer' as TabType,
      label: 'Answer',
      content: answerContent,
      disabled: !answerContent,
    },
    {
      id: 'sources' as TabType,
      label: 'Sources',
      content: sourcesContent,
      disabled: !sourcesContent,
    },
    {
      id: 'steps' as TabType,
      label: 'Steps',
      content: thinkingContent,
      disabled: !thinkingContent,
    },
  ];

  // Auto-select the first tab with content, prioritizing Answer > Steps > Sources
  const getInitialTab = (): TabType => {
    if (answerContent) return 'answer';
    if (thinkingContent) return 'steps';
    if (sourcesContent) return 'sources';
    return 'answer'; // fallback
  };

  const [activeTab, setActiveTab] = useState<TabType>(getInitialTab());

  // Update active tab when content changes (for streaming responses)
  useEffect(() => {
    const newInitialTab = getInitialTab();
    if (newInitialTab !== activeTab) {
      setActiveTab(newInitialTab);
    }
  }, [content]);

  // Check if we're in a streaming state (content is being built up)
  const isStreaming = content.includes('<thinking>') && !answerContent && thinkingContent;

  return (
    <div className='w-full'>
      {/* Tab Navigation */}
      <div className='flex border-b border-border mb-4'>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            disabled={tab.disabled}
            className={`flex items-center space-x-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            } ${tab.disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          >
            {tab.id === 'sources' && (
              <svg width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='currentColor' strokeWidth='2'>
                <circle cx='12' cy='12' r='3' />
                <path d='M12 1v6m0 6v6' />
                <path d='M3 12h6m6 0h6' />
              </svg>
            )}
            {tab.id === 'steps' && (
              <svg width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='currentColor' strokeWidth='2'>
                <path d='M5 12h14' />
                <path d='M12 5l7 7-7 7' />
              </svg>
            )}
            <span>{tab.label}</span>
            {/* Show streaming indicator on Steps tab when thinking */}
            {tab.id === 'steps' && isStreaming && (
              <div className='flex space-x-1'>
                <div className='w-1.5 h-1.5 bg-primary rounded-full animate-pulse'></div>
                <div
                  className='w-1.5 h-1.5 bg-primary rounded-full animate-pulse'
                  style={{ animationDelay: '0.2s' }}
                ></div>
                <div
                  className='w-1.5 h-1.5 bg-primary rounded-full animate-pulse'
                  style={{ animationDelay: '0.4s' }}
                ></div>
              </div>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className='min-h-[100px]'>
        {tabs.map((tab) => (
          <div key={tab.id} className={`${activeTab === tab.id ? 'block' : 'hidden'}`}>
            {tab.content ? (
              <div className='prose prose-sm max-w-none whitespace-pre-wrap break-words'>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{tab.content}</ReactMarkdown>
              </div>
            ) : (
              <div className='text-muted-foreground text-sm'>
                {tab.id === 'answer' && 'No answer content available'}
                {tab.id === 'sources' && 'No sources available'}
                {tab.id === 'steps' && 'No steps available'}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Streaming indicator for Answer tab when thinking is happening */}
      {activeTab === 'answer' && isStreaming && (
        <div className='mt-4 p-3 bg-muted/50 rounded-lg border border-dashed border-muted-foreground/30'>
          <div className='flex items-center space-x-2 text-sm text-muted-foreground'>
            <div className='flex space-x-1'>
              <div className='w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:-0.3s]'></div>
              <div className='w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:-0.15s]'></div>
              <div className='w-2 h-2 bg-primary rounded-full animate-bounce'></div>
            </div>
            <span>RAGBot is thinking and building the answer...</span>
          </div>
        </div>
      )}
    </div>
  );
}
