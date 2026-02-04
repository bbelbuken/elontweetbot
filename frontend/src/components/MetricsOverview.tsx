import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';

interface MetricsOverviewProps {
    className?: string;
}

export function MetricsOverview({ className = '' }: MetricsOverviewProps) {
    const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [manualMode, setManualMode] = useState(false);

    useEffect(() => {
        fetchMetrics();
        // Refresh metrics every 15 seconds
        const interval = setInterval(fetchMetrics, 15000);
        return () => clearInterval(interval);
    }, []);

    const fetchMetrics = async () => {
        try {
            setError(null);
            const data = await apiClient.getMetrics();
            setMetrics(data);
        } catch (err) {
            setError('Failed to fetch metrics');
            console.error('Error fetching metrics:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleToggleOverride = async () => {
        try {
            const result = await apiClient.toggleOverride();
            setManualMode(result.manual_mode);
        } catch (err) {
            console.error('Error toggling override:', err);
        }
    };

    const getPnlColor = (pnl: number) => {
        if (pnl > 0) return 'text-green-600';
        if (pnl < 0) return 'text-red-600';
        return 'text-gray-600';
    };

    const getStatusColor = (status: string) => {
        return status === 'healthy'
            ? 'text-green-600 bg-green-100'
            : 'text-red-600 bg-red-100';
    };

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }).format(amount);
    };

    if (loading) {
        return (
            <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
                <h2 className='text-lg font-semibold text-gray-900 mb-4'>
                    System Metrics
                </h2>
                <div className='grid grid-cols-2 md:grid-cols-4 gap-4'>
                    {[...Array(4)].map((_, i) => (
                        <div key={i} className='animate-pulse'>
                            <div className='h-4 bg-gray-200 rounded w-3/4 mb-2'></div>
                            <div className='h-6 bg-gray-200 rounded w-1/2'></div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    if (error || !metrics) {
        return (
            <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
                <h2 className='text-lg font-semibold text-gray-900 mb-4'>
                    System Metrics
                </h2>
                <div className='text-center py-8'>
                    <div className='text-red-600 mb-2'>
                        {error || 'No metrics available'}
                    </div>
                    <button
                        onClick={fetchMetrics}
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
                        System Metrics
                    </h2>
                    <div className='flex items-center space-x-3'>
                        <span
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                                metrics.system_status,
                            )}`}
                        >
                            {metrics.system_status.toUpperCase()}
                        </span>
                        <button
                            onClick={handleToggleOverride}
                            className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                                manualMode
                                    ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200'
                                    : 'bg-green-100 text-green-800 hover:bg-green-200'
                            }`}
                        >
                            {manualMode ? 'Manual Mode' : 'Auto Mode'}
                        </button>
                    </div>
                </div>
            </div>

            <div className='p-6'>
                <div className='grid grid-cols-2 md:grid-cols-4 gap-6'>
                    <div className='text-center'>
                        <div className='text-2xl font-bold text-gray-900'>
                            {metrics.tweets_processed.toLocaleString()}
                        </div>
                        <div className='text-sm text-gray-500'>
                            Tweets Processed
                        </div>
                    </div>

                    <div className='text-center'>
                        <div className='text-2xl font-bold text-gray-900'>
                            {metrics.trades_executed.toLocaleString()}
                        </div>
                        <div className='text-sm text-gray-500'>
                            Trades Executed
                        </div>
                    </div>

                    <div className='text-center'>
                        <div className='text-2xl font-bold text-gray-900'>
                            {metrics.open_positions}
                        </div>
                        <div className='text-sm text-gray-500'>
                            Open Positions
                        </div>
                    </div>

                    <div className='text-center'>
                        <div
                            className={`text-2xl font-bold ${getPnlColor(metrics.current_pnl)}`}
                        >
                            {formatCurrency(metrics.current_pnl)}
                        </div>
                        <div className='text-sm text-gray-500'>Current P&L</div>
                    </div>
                </div>

                <div className='mt-6 pt-6 border-t border-gray-200'>
                    <div className='flex items-center justify-between'>
                        <span className='text-sm text-gray-500'>Daily P&L</span>
                        <span
                            className={`text-lg font-semibold ${getPnlColor(metrics.daily_pnl)}`}
                        >
                            {formatCurrency(metrics.daily_pnl)}
                        </span>
                    </div>
                </div>

                <div className='mt-4'>
                    <button
                        onClick={fetchMetrics}
                        className='w-full text-center text-sm text-primary-600 hover:text-primary-700 font-medium py-2'
                    >
                        Refresh Metrics
                    </button>
                </div>
            </div>
        </div>
    );
}
