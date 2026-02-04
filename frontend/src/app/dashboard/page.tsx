'use client';

import { TweetFeed } from '@/components/TweetFeed';
import { PositionsOverview } from '@/components/PositionsOverview';
import { MetricsOverview } from '@/components/MetricsOverview';
import { TradeHistory } from '@/components/TradeHistory';

export default function DashboardPage() {
    return (
        <div className='min-h-screen bg-gray-50'>
            <div className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8'>
                {/* Header */}
                <div className='mb-8'>
                    <h1 className='text-3xl font-bold text-gray-900'>
                        Trading Dashboard
                    </h1>
                    <p className='mt-2 text-gray-600'>
                        Monitor your crypto trading bot performance and recent
                        activity
                    </p>
                </div>

                {/* Metrics Overview */}
                <div className='mb-8'>
                    <MetricsOverview />
                </div>

                {/* Main Content Grid */}
                <div className='grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8'>
                    {/* Tweet Feed */}
                    <TweetFeed />

                    {/* Positions Overview */}
                    <PositionsOverview />
                </div>

                {/* Trade History */}
                <div className='mb-8'>
                    <TradeHistory limit={20} />
                </div>
            </div>
        </div>
    );
}
