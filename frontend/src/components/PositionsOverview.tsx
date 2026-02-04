import { useState, useCallback } from 'react';
import { apiClient } from '@/lib/api';
import { formatCurrency, formatDate, getPnlColor } from '@/lib/utils';
import { useRealTimeData } from '@/hooks/useRealTimeData';

export function PositionsOverview({ className = '' }: PositionsOverviewProps) {
    const fetchPositions = useCallback(async () => {
        return await apiClient.getPositions();
    }, []);

    const {
        data: positions,
        loading,
        error,
        lastUpdated,
        refresh,
    } = useRealTimeData({
        fetchFunction: fetchPositions,
        interval: 10000, // 10 seconds
    });

    const totalUnrealizedPnl =
        positions?.reduce((sum, pos) => sum + (pos.unrealized_pnl || 0), 0) ||
        0;

    if (loading) {
        return (
            <div
                className={`bg-white rounded-lg shadow p-4 sm:p-6 ${className}`}
            >
                <h2 className='text-lg font-semibold text-gray-900 mb-4'>
                    Current Positions
                </h2>
                <div className='space-y-4'>
                    {[...Array(2)].map((_, i) => (
                        <div key={i} className='animate-pulse'>
                            <div className='h-4 bg-gray-200 rounded w-1/3 mb-2'></div>
                            <div className='h-3 bg-gray-200 rounded w-full mb-1'></div>
                            <div className='h-3 bg-gray-200 rounded w-2/3'></div>
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
                    Current Positions
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
                <div className='flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4'>
                    <div>
                        <h2 className='text-lg font-semibold text-gray-900'>
                            Current Positions ({positions?.length || 0})
                        </h2>
                        {lastUpdated && (
                            <p className='text-xs text-gray-500 mt-1'>
                                Last updated: {lastUpdated.toLocaleTimeString()}
                            </p>
                        )}
                    </div>
                    <div className='text-left sm:text-right'>
                        <div className='text-sm text-gray-500'>
                            Total Unrealized P&L
                        </div>
                        <div
                            className={`text-lg font-semibold ${getPnlColor(totalUnrealizedPnl)}`}
                        >
                            {formatCurrency(totalUnrealizedPnl)}
                        </div>
                    </div>
                </div>
            </div>

            <div className='p-4 sm:p-6'>
                {!positions || positions.length === 0 ? (
                    <div className='text-center py-8 text-gray-500'>
                        No open positions
                    </div>
                ) : (
                    <div className='space-y-4'>
                        {positions.map((position) => (
                            <div
                                key={position.id}
                                className='border border-gray-200 rounded-lg p-3 sm:p-4 hover:bg-gray-50 transition-colors'
                            >
                                <div className='flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-3'>
                                    <div className='flex items-center space-x-3'>
                                        <h3 className='text-lg font-semibold text-gray-900'>
                                            {position.symbol}
                                        </h3>
                                        <span className='inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800'>
                                            {position.leverage}x
                                        </span>
                                    </div>
                                    <div className='text-left sm:text-right'>
                                        <div className='text-sm text-gray-500'>
                                            Unrealized P&L
                                        </div>
                                        <div
                                            className={`text-lg font-semibold ${getPnlColor(position.unrealized_pnl || 0)}`}
                                        >
                                            {formatCurrency(
                                                position.unrealized_pnl || 0,
                                            )}
                                        </div>
                                    </div>
                                </div>

                                <div className='grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm'>
                                    <div>
                                        <div className='text-gray-500'>
                                            Size
                                        </div>
                                        <div className='font-medium'>
                                            <span className='hidden sm:inline'>
                                                {position.size.toFixed(8)}
                                            </span>
                                            <span className='sm:hidden'>
                                                {position.size.toFixed(4)}
                                            </span>
                                        </div>
                                    </div>
                                    <div>
                                        <div className='text-gray-500'>
                                            Avg Entry
                                        </div>
                                        <div className='font-medium'>
                                            {formatCurrency(position.avg_entry)}
                                        </div>
                                    </div>
                                    <div>
                                        <div className='text-gray-500'>
                                            Leverage
                                        </div>
                                        <div className='font-medium'>
                                            {position.leverage}x
                                        </div>
                                    </div>
                                    <div>
                                        <div className='text-gray-500'>
                                            Updated
                                        </div>
                                        <div className='font-medium'>
                                            {position.updated_at ? (
                                                <>
                                                    <span className='hidden sm:inline'>
                                                        {formatDate(
                                                            position.updated_at,
                                                        )}
                                                    </span>
                                                    <span className='sm:hidden'>
                                                        {new Date(
                                                            position.updated_at,
                                                        ).toLocaleDateString()}
                                                    </span>
                                                </>
                                            ) : (
                                                'N/A'
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                <div className='mt-4 pt-4 border-t border-gray-200'>
                    <button
                        onClick={refresh}
                        className='w-full text-center text-sm text-blue-600 hover:text-blue-700 font-medium py-2 hover:bg-blue-50 rounded-md transition-colors'
                    >
                        Refresh Positions
                    </button>
                </div>
            </div>
        </div>
    );
}
