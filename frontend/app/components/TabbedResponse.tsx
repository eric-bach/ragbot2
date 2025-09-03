'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ThumbsUp, ThumbsDown, Copy, ChevronDown, ChevronUp, Sparkles, Link, Brain } from 'lucide-react';
import AnimatedLogo from './AnimatedLogo';

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  isStreaming?: boolean;
}

interface TabbedResponseProps {
  message: Message;
}

export default function TabbedResponse({ message }: TabbedResponseProps) {
  const { content } = message;

  // Extract all thinking content (steps) - handle multiple occurrences
  const thinkingMatches = Array.from(content.matchAll(/<thinking>([\s\S]*?)<\/thinking>/g));
  const thinkingContent = thinkingMatches
    .map((match) => match[1].trim())
    .filter((content) => content.length > 0)
    .join('\n\n');

  // Extract all sources content - handle multiple occurrences
  const sourcesMatches = Array.from(content.matchAll(/<sources>([\s\S]*?)<\/sources>/g));
  const rawSourcesContent = sourcesMatches
    .map((match) => match[1].trim())
    .filter((content) => content.length > 0)
    .join('\n\n');

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

  // Extract all response content - handle multiple occurrences
  const responseMatches = Array.from(content.matchAll(/<response>([\s\S]*?)<\/response>/g));
  const structuredAnswerContent =
    responseMatches.length > 0
      ? responseMatches
          .map((match) => match[1].trim())
          .filter((content) => content.length > 0)
          .join('\n\n')
      : '';

  // For answer content, show structured content if available, otherwise show raw content
  // When streaming, show raw content if no structured content exists yet
  const cleanContent = content
    .replace(/<thinking>[\s\S]*?<\/thinking>/g, '')
    .replace(/<sources>[\s\S]*?<\/sources>/g, '')
    .replace(/<response>[\s\S]*?<\/response>/g, '')
    .trim();

  const answerContent = structuredAnswerContent || cleanContent;

  // Use the isStreaming property from the message instead of calculating it
  const isStreaming = message.isStreaming || false;

  // State for managing collapsible sections
  const [expandedSections, setExpandedSections] = useState({
    thinking: true, // Start expanded during streaming
    sources: false, // Start collapsed
  });

  // Collapse thinking section when streaming completes
  useEffect(() => {
    if (!isStreaming) {
      setExpandedSections((prev) => ({
        ...prev,
        thinking: false,
      }));
    }
  }, [isStreaming]);

  // Toggle section expansion
  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  // Copy text functionality
  const handleCopyText = async () => {
    let textToCopy = '';

    if (isStreaming) {
      // When streaming, copy the current content (thinking + answer)
      const parts = [];
      if (thinkingContent) parts.push(`**Thinking:**\n${thinkingContent}`);
      if (answerContent) parts.push(`**Response:**\n${answerContent}`);
      textToCopy = parts.join('\n\n') || content;
    } else {
      // When not streaming, copy all available content
      const parts = [];
      if (answerContent) parts.push(`**Response:**\n${answerContent}`);
      if (sourcesContent) parts.push(`**Sources:**\n${sourcesContent}`);
      if (thinkingContent) parts.push(`**Thinking:**\n${thinkingContent}`);
      textToCopy = parts.join('\n\n');
    }

    if (textToCopy) {
      try {
        await navigator.clipboard.writeText(textToCopy);
        // You could add a toast notification here if desired
      } catch (err) {
        console.error('Failed to copy text: ', err);
      }
    }
  };

  // Feedback handlers (for future implementation)
  const handleThumbsUp = () => {
    // TODO: Implement feedback functionality
    console.log('Thumbs up clicked');
  };

  const handleThumbsDown = () => {
    // TODO: Implement feedback functionality
    console.log('Thumbs down clicked');
  };

  // Collapsible section component
  const CollapsibleSection = ({
    title,
    content,
    isExpanded,
    onToggle,
    icon,
    isStreaming: sectionStreaming = false,
  }: {
    title: string;
    content: string;
    isExpanded: boolean;
    onToggle: () => void;
    icon?: React.ReactNode;
    isStreaming?: boolean;
  }) => {
    if (!content && !sectionStreaming) return null;

    return (
      <div className='mb-4'>
        <button
          onClick={onToggle}
          className='flex items-center justify-between w-full text-left text-sm font-medium text-muted-foreground hover:text-foreground transition-colors py-2'
        >
          <div className='flex items-center space-x-2'>
            {icon}
            <span>{title}</span>
            {sectionStreaming && (
              <div className='flex space-x-1 ml-2'>
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
          </div>
          {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>

        {isExpanded && (
          <div className='mt-2 border-l-2 border-muted pl-3'>
            {content ? (
              <div className='prose prose-sm max-w-none whitespace-pre-wrap break-words'>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
              </div>
            ) : sectionStreaming ? (
              <div className='text-muted-foreground text-sm italic'>Waiting for content...</div>
            ) : null}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className='w-full'>
      {/* Show cooking animation when streaming */}
      {isStreaming && (
        <div className='flex items-center space-x-2 text-sm text-muted-foreground pt-2 mb-4'>
          <Image
            src='/logo.png'
            alt='RAGBot Logo'
            className='w-4 h-4 animate-bounce'
            style={{ animationDelay: '-0.3s' }}
            width={6}
            height={6}
          />
          <AnimatedLogo text='RAGBot 2' isAnimating={true} size='sm' />
          <span>is cooking...</span>
        </div>
      )}

      {/* Collapsible Sections */}
      <div className='min-h-[100px]'>
        {/* Thinking Section */}
        <CollapsibleSection
          title='Thinking'
          content={thinkingContent}
          isExpanded={expandedSections.thinking}
          onToggle={() => toggleSection('thinking')}
          isStreaming={isStreaming && !answerContent} // Show streaming when thinking but no answer yet
          icon={<Brain width={18} height={18} />}
        />

        {/* Response Section - Always expanded, not collapsible */}
        {answerContent && (
          <div className='mb-4'>
            <div className='flex items-center space-x-2 text-md text-muted-foreground hover:text-foreground py-2'>
              <Sparkles width={18} height={18} />
              <span>Response</span>
            </div>

            <div className='border-l-2 border-muted pl-3'>
              <div className='prose prose-sm max-w-none whitespace-pre-wrap break-words'>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{answerContent}</ReactMarkdown>
              </div>
            </div>
          </div>
        )}

        {/* Sources Section */}
        <CollapsibleSection
          title={`Sources (${sourcesMatches.length})`}
          content={sourcesContent}
          isExpanded={expandedSections.sources}
          onToggle={() => toggleSection('sources')}
          icon={<Link width={18} height={18} />}
        />
      </div>

      {/* Feedback Buttons */}
      <div className='flex items-center justify-between mt-2 pt-2 border-t border-border'>
        <div className='text-xs opacity-70'>{message.timestamp.toLocaleTimeString()}</div>
        {!isStreaming && (
          <div className='flex items-center space-x-1'>
            <button
              onClick={handleThumbsUp}
              className='p-1.5 hover:bg-muted rounded transition-all duration-200 cursor-pointer hover:scale-105'
              title='Thumbs up'
            >
              <ThumbsUp size={14} className='transition-colors duration-200 hover:text-primary' />
            </button>
            <button
              onClick={handleThumbsDown}
              className='p-1.5 hover:bg-muted rounded transition-all duration-200 cursor-pointer hover:scale-105'
              title='Thumbs down'
            >
              <ThumbsDown size={14} className='transition-colors duration-200 hover:text-primary' />
            </button>
            <button
              onClick={handleCopyText}
              className='p-1.5 hover:bg-muted rounded transition-all duration-200 cursor-pointer hover:scale-105'
              title='Copy text'
            >
              <Copy size={14} className='transition-colors duration-200 hover:text-primary' />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
