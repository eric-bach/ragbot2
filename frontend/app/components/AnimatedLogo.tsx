'use client';

interface AnimatedLogoProps {
  text?: string;
  isAnimating?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export default function AnimatedLogo({ text = 'RAGBot 2', isAnimating = false, size = 'md' }: AnimatedLogoProps) {
  // Split text into individual characters, preserving spaces
  const characters = text.split('');

  const sizeClasses = {
    sm: 'text-sm font-medium',
    md: 'text-xl font-semibold',
    lg: 'text-2xl font-bold',
  };

  return (
    <span className={`${sizeClasses[size]} flex`}>
      {characters.map((char, index) => (
        <span
          key={index}
          className={`inline-block ${isAnimating ? 'animate-bounce' : ''}`}
          style={{
            animationDelay: isAnimating ? `${index * 0.1}s` : '0s',
            // Preserve space width for space characters
            minWidth: char === ' ' ? '0.25rem' : 'auto',
          }}
        >
          {char === ' ' ? '\u00A0' : char}
        </span>
      ))}
    </span>
  );
}
