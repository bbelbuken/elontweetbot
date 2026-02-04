import { useState, useCallback } from 'react';
import { apiClient } from '@/lib/api';
import { formatCurrency, getPnlColor } from '@/lib/utils';
import { useRealTimeData } from '@/hooks/useRealTimeData';

export function MetricsOverview({ className = '' }: MetricsOverviewProps) {
    const [manualMode, setManualMode] = useState(false);

    const fetchMetrics = useCallback(async () => {
        return await apiClient.getMetrics();
    }, []);

    const {
        data: metrics,
        loading,
        error,
        lastUpdated,
        refresh,
    } = useRealTimeData({
        fetchFunction: fetchMetrics,
        interval: 10000, // 10 seconds
    });

    const handleToggleOverride = async () => {
        try {
            const result = await apiClient.toggleOverride();
            setManualMode(result.manual_mode);
        } catch (err) {
            console.error('Error toggling override:', err);
        }
    };

    const getStatusColor = (status: string) => {
        return status === 'healthy'
            ? 'text-green-600 bg-green-100'
            : 'text-red-600 bg-red-100';
    };

    if (loading) {
        return (
            <div
                className={`bg-white rounded-lg shadow p-4 sm:p-6 ${className}`}
            >
                <h2 className='text-lg font-semibold text-gray-900 mb-4'>
                    System Metrics
                </h2>
                <div className='grid grid-cols-2 sm:grid-cols-4 gap-4'>
                    {[...Array(4)].map((_, i) => (
                        <div key={i} className='animate-pulse text-center'>
                            <div className='h-4 bg-gray-200 rounded w-3/4 mx-auto mb-2'></div>
                            <div className='h-6 bg-gray-200 rounded w-1/2 mx-auto'></div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    if (error || !metrics) {
        return (
            <div
                className={`bg-white rounded-lg shadow p-4 sm:p-6 ${className}`}
            >
                <h2 className='text-lg font-semibold text-gray-900 mb-4'>
                    System Metrics
                </h2>
                <div className='text-center py-8'>
                    <div className='text-red-600 mb-2'>
                        {error || 'No metrics available'}
                    </div>
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
                <div className='flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4'>
                    <div>
                        <h2 className='text-lg font-semibold text-gray-900'>
                            System Metrics
                        </h2>
                        {lastUpdated && (
                            <p className='text-xs text-gray-500 mt-1'>
                                Last updated: {lastUpdated.toLocaleTimeString()}
                            </p>
                        )}
                    </div>
                    <div className='flex flex-col sm:flex-row items-start sm:items-center gap-3'>
                        <span
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                                metrics.system_status,
                            )}`}
                        >
                            <div
                                className={`w-2 h-2 rounded-full mr-1.5 ${
                                    metrics.system_status === 'healthy'
                                        ? 'bg-green-400'
                                        : 'bg-red-400'
                                }`}
                            />
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

            <div className='p-4 sm:p-6'>
                <div className='grid grid-cols-2 sm:grid-cols-4 gap-4 sm:gap-6'>
                    <div className='text-center'>
                        <div className='text-xl sm:text-2xl font-bold text-gray-900'>
                            {metrics.tweets_processed.toLocaleString()}
                        </div>
                        <div className='text-xs sm:text-sm text-gray-500 mt-1'>
                            Tweets Processed
                        </div>
                    </div>

                    <div className='text-center'>
                        <div className='text-xl sm:text-2xl font-bold text-gray-900'>
                            {metrics.trades_executed.toLocaleString()}
                        </div>
                        <div className='text-xs sm:text-sm text-gray-500 mt-1'>
                            Trades Executed
                        </div>
                    </div>

                    <div className='text-center'>
                        <div className='text-xl sm:text-2xl font-bold text-gray-900'>
                            {metrics.open_positions}
                        </div>
                        <div className='text-xs sm:text-sm text-gray-500 mt-1'>
                            Open Positions
                        </div>
                    </div>

                    <div className='text-center'>
                        <div
                            className={`text-xl sm:text-2xl font-bold ${getPnlColor(metrics.current_pnl)}`}
                        >
                            {formatCurrency(metrics.current_pnl)}
                        </div>
                        <div className='text-xs sm:text-sm text-gray-500 mt-1'>
                            Current P&L
                        </div>
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
                        onClick={refresh}
                        className='w-full text-center text-sm text-blue-600 hover:text-blue-700 font-medium py-2 hover:bg-blue-50 rounded-md transition-colors'
                    >
                        Refresh Metrics
                    </button>
                </div>
            </div>
        </div>
    );
}
