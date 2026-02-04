import { useState, useCallback } from 'react';
import { apiClient } from '@/lib/api';
import {
    formatDate,
    getSignalScoreColor,
    getSentimentColor,
} from '@/lib/utils';
import { useRealTimeData } from '@/hooks/useRealTimeData';

export function TweetFeed({ className = '' }: TweetFeedProps) {
    const fetchTweets = useCallback(async () => {
        return await apiClient.getTweets(20);
    }, []);

    const {
        data: tweets,
        loading,
        error,
        lastUpdated,
        refresh,
    } = useRealTimeData({
        fetchFunction: fetchTweets,
        interval: 20000, // 20 seconds
    });

    if (loading) {
        return (
            <div
                className={`bg-white rounded-lg shadow p-4 sm:p-6 ${className}`}
            >
                <h2 className='text-lg font-semibold text-gray-900 mb-4'>
                    Recent Tweets
                </h2>
                <div className='space-y-4'>
                    {[...Array(3)].map((_, i) => (
                        <div key={i} className='animate-pulse'>
                            <div className='h-4 bg-gray-200 rounded w-1/4 mb-2'></div>
                            <div className='h-3 bg-gray-200 rounded w-full mb-1'></div>
                            <div className='h-3 bg-gray-200 rounded w-3/4'></div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div
                className={`bg-white rounded-lg shadow p-4 sm:p-6 ${className}`}
            >
                <h2 className='text-lg font-semibold text-gray-900 mb-4'>
                    Recent Tweets
                </h2>
                <div className='text-center py-8'>
                    <div className='text-red-600 mb-2'>{error}</div>
                    <button
                        onClick={refresh}
                        className='text-blue-600 hover:text-blue-700 font-medium'
                    >
                        Try Again
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className={`bg-white rounded-lg shadow ${className}`}>
            <div className='p-4 sm:p-6 border-b border-gray-200'>
                <div className='flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2'>
                    <div>
                        <h2 className='text-lg font-semibold text-gray-900'>
                            Recent Tweets ({tweets?.length || 0})
                        </h2>
                        {lastUpdated && (
                            <p className='text-xs text-gray-500 mt-1'>
                                Last updated: {lastUpdated.toLocaleTimeString()}
                            </p>
                        )}
                    </div>
                    <button
                        onClick={refresh}
                        className='text-sm text-blue-600 hover:text-blue-700 font-medium px-3 py-1 hover:bg-blue-50 rounded-md transition-colors'
                    >
                        Refresh
                    </button>
                </div>
            </div>

            <div className='max-h-96 overflow-y-auto'>
                {!tweets || tweets.length === 0 ? (
                    <div className='p-6 text-center text-gray-500'>
                        No tweets available
                    </div>
                ) : (
                    <div className='divide-y divide-gray-200'>
                        {tweets.map((tweet) => (
                            <div
                                key={tweet.id}
                                className='p-3 sm:p-4 hover:bg-gray-50 transition-colors'
                            >
                                <div className='flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2 mb-2'>
                                    <div className='flex items-center space-x-2'>
                                        <span className='font-medium text-gray-900 text-sm'>
                                            @{tweet.author}
                                        </span>
                                        <span className='text-xs text-gray-500'>
                                            {new Date(
                                                tweet.created_at,
                                            ).toLocaleDateString()}
                                            <span className='hidden sm:inline'>
                                                {' '}
                                                {new Date(
                                                    tweet.created_at,
                                                ).toLocaleTimeString([], {
                                                    hour: '2-digit',
                                                    minute: '2-digit',
                                                })}
                                            </span>
                                        </span>
                                    </div>
                                    <div className='flex items-center space-x-2'>
                                        <span
                                            className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getSignalScoreColor(
                                                tweet.signal_score,
                                            )}`}
                                        >
                                            Signal: {tweet.signal_score}
                                        </span>
                                    </div>
                                </div>

                                <p className='text-gray-800 mb-2 text-sm leading-relaxed'>
                                    {tweet.text}
                                </p>

                                <div className='flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 text-xs'>
                                    <span
                                        className={`font-medium ${getSentimentColor(tweet.sentiment_score)}`}
                                    >
                                        Sentiment:{' '}
                                        {tweet.sentiment_score > 0 ? '+' : ''}
                                        {tweet.sentiment_score.toFixed(3)}
                                    </span>
                                    <span className='text-gray-500'>
                                        ID: {tweet.id}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
