import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import {
    formatDate,
    getSignalScoreColor,
    getSentimentColor,
} from '@/lib/utils';

export function TweetFeed({ className = '' }: TweetFeedProps) {
    const [tweets, setTweets] = useState<TweetWithSignal[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchTweets();
        // Refresh tweets every 30 seconds
        const interval = setInterval(fetchTweets, 30000);
        return () => clearInterval(interval);
    }, []);

    const fetchTweets = async () => {
        try {
            setError(null);
            const data = await apiClient.getTweets(20);
            setTweets(data);
        } catch (err) {
            setError('Failed to fetch tweets');
            console.error('Error fetching tweets:', err);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
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
            <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
                <h2 className='text-lg font-semibold text-gray-900 mb-4'>
                    Recent Tweets
                </h2>
                <div className='text-center py-8'>
                    <div className='text-red-600 mb-2'>{error}</div>
                    <button
                        onClick={fetchTweets}
                        className='text-primary-600 hover:text-primary-700 font-medium'
                    >
                        Try Again
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className={`bg-white rounded-lg shadow ${className}`}>
            <div className='p-6 border-b border-gray-200'>
                <div className='flex items-center justify-between'>
                    <h2 className='text-lg font-semibold text-gray-900'>
                        Recent Tweets
                    </h2>
                    <button
                        onClick={fetchTweets}
                        className='text-sm text-primary-600 hover:text-primary-700 font-medium'
                    >
                        Refresh
                    </button>
                </div>
            </div>

            <div className='max-h-96 overflow-y-auto'>
                {tweets.length === 0 ? (
                    <div className='p-6 text-center text-gray-500'>
                        No tweets available
                    </div>
                ) : (
                    <div className='divide-y divide-gray-200'>
                        {tweets.map((tweet) => (
                            <div
                                key={tweet.id}
                                className='p-4 hover:bg-gray-50'
                            >
                                <div className='flex items-start justify-between mb-2'>
                                    <div className='flex items-center space-x-2'>
                                        <span className='font-medium text-gray-900'>
                                            @{tweet.author}
                                        </span>
                                        <span className='text-sm text-gray-500'>
                                            {formatDate(tweet.created_at)}
                                        </span>
                                    </div>
                                    <div className='flex items-center space-x-2'>
                                        <span
                                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSignalScoreColor(
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

                                <div className='flex items-center justify-between text-xs'>
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
