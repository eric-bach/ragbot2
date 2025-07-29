'use client';

import React from 'react';
import {
  Authenticator,
  Button,
  Heading,
  Image,
  Theme,
  ThemeProvider,
  useAuthenticator,
  useTheme,
  View,
} from '@aws-amplify/ui-react';
import { Amplify } from 'aws-amplify';
import { ResourcesConfig } from '@aws-amplify/core';
import { AuthUser } from 'aws-amplify/auth';
import { AuthEventData } from '@aws-amplify/ui';

import '@aws-amplify/ui-react/styles.css';

interface ChatLayoutProps {
  children: React.ReactNode;
  signOut?: ((data?: AuthEventData | undefined) => void) | undefined;
  user?: AuthUser | undefined;
}

function ChatLayout({ children, signOut, user }: ChatLayoutProps) {
  if (!signOut || !user) {
    return <>{children}</>;
  }

  return (
    <div className='h-screen flex flex-col'>
      {/* Navbar */}
      <nav className='flex-shrink-0 bg-card border-b border-border px-4 py-3'>
        <div className='max-w-4xl mx-auto flex items-center justify-between'>
          <div className='flex items-center space-x-3'>
            <h1 className='text-xl font-semibold'>RAGBot Chat</h1>
          </div>
          <div className='flex items-center space-x-4'>
            <span className='text-sm text-muted-foreground'>
              Welcome, {user.signInDetails?.loginId || user.username}
            </span>
            <button
              onClick={() => signOut()}
              className='px-3 py-1.5 text-sm bg-secondary text-secondary-foreground hover:bg-secondary/80 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2'
            >
              Sign Out
            </button>
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className='flex-1 overflow-hidden'>{children}</div>
    </div>
  );
}

const config: ResourcesConfig = {
  Auth: {
    Cognito: {
      userPoolId: process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID!,
      userPoolClientId: process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID!,
    },
  },
};

Amplify.configure(config, { ssr: true });

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const { tokens } = useTheme();

  const theme: Theme = {
    name: 'Auth Theme',
    tokens: {
      components: {
        authenticator: {
          router: {
            boxShadow: `0 0 16px ${tokens.colors.overlay['10']}`,
            borderWidth: '0',
          },
          form: {
            padding: `${tokens.space.medium} ${tokens.space.xl} ${tokens.space.medium}`,
          },
        },
        button: {
          primary: {
            backgroundColor: '#256aac',
          },
          link: {
            color: '#256aac',
          },
        },
        fieldcontrol: {
          _focus: {
            boxShadow: `0 0 0 2px #256aac`,
          },
        },
        tabs: {
          item: {
            color: tokens.colors.neutral['80'],
            _active: {
              borderColor: tokens.colors.neutral['100'],
              color: '#256aac',
            },
          },
        },
      },
    },
  };

  const components = {
    Header() {
      const { tokens } = useTheme();

      return (
        <View textAlign='center' padding={tokens.space.large} paddingTop='6rem'>
          <Image alt='RAGBot 2' src='logo.png' width={54} />
          <Heading level={4}>RAGBot 2</Heading>
        </View>
      );
    },

    SignIn: {
      Header() {
        const { tokens } = useTheme();

        return (
          <Heading padding={`${tokens.space.xl} 0 0 ${tokens.space.xl}`} level={4}>
            Sign in to your account
          </Heading>
        );
      },
      Footer() {
        const { toForgotPassword } = useAuthenticator();

        return (
          <View textAlign='center'>
            <Button fontWeight='normal' onClick={toForgotPassword} size='small' variation='link'>
              Reset Password
            </Button>
          </View>
        );
      },
    },

    SignUp: {
      Header() {
        const { tokens } = useTheme();

        return (
          <Heading padding={`${tokens.space.xl} 0 0 ${tokens.space.xl}`} level={4}>
            Create a new account
          </Heading>
        );
      },
      Footer() {
        const { toSignIn } = useAuthenticator();

        return (
          <View textAlign='center'>
            <Button fontWeight='normal' onClick={toSignIn} size='small' variation='link'>
              Back to Sign In
            </Button>
          </View>
        );
      },
    },
  };

  const formFields = {
    signUp: {
      username: {
        label: 'Email:',
        placeholder: 'Enter your email',
        order: 1,
      },
      password: {
        order: 2,
      },
      confirm_password: {
        order: 3,
      },
    },
  };

  return (
    <ThemeProvider theme={theme}>
      <Authenticator formFields={formFields} components={components}>
        {({ signOut, user }) => (
          <ChatLayout signOut={signOut} user={user}>
            {children}
          </ChatLayout>
        )}
      </Authenticator>
    </ThemeProvider>
  );
}
