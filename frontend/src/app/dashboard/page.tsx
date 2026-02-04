'use client';

import { TweetFeed } from '@/components/TweetFeed';
import { PositionsOverview } from '@/components/PositionsOverview';
import { MetricsOverview } from '@/components/MetricsOverview';
import { TradeHistory } from '@/components/TradeHistory';
import { PnLChart } from '@/components/PnLChart';

export default function DashboardPage() {
    return (
        <div className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-8'>
            {/* Header */}
            <div className='mb-6 sm:mb-8'>
                <div className='flex items-center gap-3 mb-2'>
                    <div className='w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center'>
                        <img
                            src='/favicon.svg'
                            alt='CryptoBot'
                            className='w-5 h-5'
                        />
                    </div>
                    <h1 className='text-2xl sm:text-3xl font-bold text-gray-900'>
                        CryptoBot Dashboard
                    </h1>
                </div>
                <p className='mt-2 text-sm sm:text-base text-gray-600'>
                    AI-powered crypto trading with real-time sentiment analysis
                </p>
            </div>

            {/* Metrics Overview */}
            <div className='mb-6 sm:mb-8'>
                <MetricsOverview />
            </div>

            {/* P&L Chart */}
            <div className='mb-6 sm:mb-8'>
                <PnLChart />
            </div>

            {/* Main Content Grid */}
            <div className='grid grid-cols-1 xl:grid-cols-2 gap-6 sm:gap-8 mb-6 sm:mb-8'>
                {/* Tweet Feed */}
                <TweetFeed />

                {/* Positions Overview */}
                <PositionsOverview />
            </div>

            {/* Trade History */}
            <div className='mb-6 sm:mb-8'>
                <TradeHistory limit={50} />
            </div>
        </div>
    );
}
