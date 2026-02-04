import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';

interface PositionsOverviewProps {
    className?: string;
}

export function PositionsOverview({ className = '' }: PositionsOverviewProps) {
    const [positions, setPositions] = useState<Position[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchPositions();
        // Refresh positions every 10 seconds
        const interval = setInterval(fetchPositions, 10000);
        return () => clearInterval(interval);
    }, []);

    const fetchPositions = async () => {
        try {
            setError(null);
            const data = await apiClient.getPositions();
            setPositions(data);
        } catch (err) {
            setError('Failed to fetch positions');
            console.error('Error fetching positions:', err);
        } finally {
            setLoading(false);
        }
    };

    const getPnlColor = (pnl: number) => {
        if (pnl > 0) return 'text-green-600';
        if (pnl < 0) return 'text-red-600';
        return 'text-gray-600';
    };

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }).format(amount);
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleString();
    };

    const totalUnrealizedPnl = positions.reduce(
        (sum, pos) => sum + (pos.unrealized_pnl || 0),
        0,
    );

    if (loading) {
        return (
            <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
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
            <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
                <h2 className='text-lg font-semibold text-gray-900 mb-4'>
                    Current Positions
                </h2>
                <div className='text-center py-8'>
                    <div className='text-red-600 mb-2'>{error}</div>
                    <button
                        onClick={fetchPositions}
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
                        Current Positions
                    </h2>
                    <div className='text-right'>
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

            <div className='p-6'>
                {positions.length === 0 ? (
                    <div className='text-center py-8 text-gray-500'>
                        No open positions
                    </div>
                ) : (
                    <div className='space-y-4'>
                        {positions.map((position) => (
                            <div
                                key={position.id}
                                className='border border-gray-200 rounded-lg p-4 hover:bg-gray-50'
                            >
                                <div className='flex items-center justify-between mb-3'>
                                    <div className='flex items-center space-x-3'>
                                        <h3 className='text-lg font-semibold text-gray-900'>
                                            {position.symbol}
                                        </h3>
                                        <span className='inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800'>
                                            {position.leverage}x
                                        </span>
                                    </div>
                                    <div className='text-right'>
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

                                <div className='grid grid-cols-2 md:grid-cols-4 gap-4 text-sm'>
                                    <div>
                                        <div className='text-gray-500'>
                                            Size
                                        </div>
                                        <div className='font-medium'>
                                            {position.size.toFixed(8)}
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
                                            {position.updated_at
                                                ? formatDate(
                                                      position.updated_at,
                                                  )
                                                : 'N/A'}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                <div className='mt-4 pt-4 border-t border-gray-200'>
                    <button
                        onClick={fetchPositions}
                        className='w-full text-center text-sm text-primary-600 hover:text-primary-700 font-medium py-2'
                    >
                        Refresh Positions
                    </button>
                </div>
            </div>
        </div>
    );
}
