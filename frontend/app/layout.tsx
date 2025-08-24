import type { Metadata } from 'next';
import { Turnstile } from '@marsidev/react-turnstile';
import { Geist, Geist_Mono } from 'next/font/google';

import './globals.css';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title: 'RAGBot 2',
  description: 'Where Knowledge Meets Action',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang='en'>
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <Turnstile siteKey={process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY || ''} />
        {children}
      </body>
    </html>
  );
}
