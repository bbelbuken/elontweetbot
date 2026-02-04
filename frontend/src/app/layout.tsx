import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
    title: 'Tweet Crypto Trading Bot',
    description:
        'AI-powered cryptocurrency trading bot driven by social media sentiment',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang='en'>
            <body className={inter.className}>
                <ErrorBoundary>
                    <div className='min-h-screen bg-gray-50'>{children}</div>
                </ErrorBoundary>
            </body>
        </html>
    );
}
