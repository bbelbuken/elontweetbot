import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
    metadataBase: new URL('https://cryptobot-dashboard.vercel.app'),
    title: 'CryptoBot Dashboard | AI-Powered Trading',
    description:
        'Real-time cryptocurrency trading bot powered by Twitter sentiment analysis and AI. Monitor trades, positions, and P&L performance.',
    keywords:
        'cryptocurrency, trading bot, AI, sentiment analysis, bitcoin, ethereum, automated trading',
    authors: [{ name: 'CryptoBot Team' }],
    creator: 'CryptoBot',
    publisher: 'CryptoBot',
    robots: 'index, follow',
    icons: {
        icon: [{ url: '/favicon.svg', sizes: 'any', type: 'image/svg+xml' }],
        apple: [
            { url: '/favicon.svg', sizes: '180x180', type: 'image/svg+xml' },
        ],
    },
    manifest: '/manifest.json',
    openGraph: {
        type: 'website',
        locale: 'en_US',
        url: 'https://cryptobot-dashboard.vercel.app',
        title: 'CryptoBot Dashboard | AI-Powered Trading',
        description:
            'Real-time cryptocurrency trading bot powered by Twitter sentiment analysis and AI.',
        siteName: 'CryptoBot Dashboard',
    },
    twitter: {
        card: 'summary_large_image',
        title: 'CryptoBot Dashboard | AI-Powered Trading',
        description:
            'Real-time cryptocurrency trading bot powered by Twitter sentiment analysis and AI.',
        creator: '@cryptobot',
    },
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
