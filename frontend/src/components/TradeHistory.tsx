import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';

interface TradeHistoryProps {
    className?: string;
    limit?: number;
}

export function TradeHistory({
    className = '',
    limit = 10,
}: TradeHistoryProps) {
    const [trades, setTrades] = useState<Trade[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchTrades();
        // Refresh trades every 30 seconds
        const interval = setInterval(fetchTrades, 30000);
        return () => clearInterval(interval);
    }, [limit]);

    const fetchTrades = async () => {
        try {
            setError(null);
            const data = await apiClient.getTrades(limit);
            setTrades(data);
        } catch (err) {
            setError('Failed to fetch trades');
            console.error('Error fetching trades:', err);
        } finally {
            setLoading(false);
        }
    };

    const getPnlColor = (pnl: number | undefined) => {
        if (!pnl) return 'text-gray-600';
        if (pnl > 0) return 'text-green-600';
        if (pnl < 0) return 'text-red-600';
        return 'text-gray-600';
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'OPEN':
                return 'bg-blue-100 text-blue-800';
            case 'CLOSED':
                return 'bg-green-100 text-green-800';
            case 'CANCELLED':
                return 'bg-red-100 text-red-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    const getSideColor = (side: string) => {
        return side === 'LONG' ? 'text-green-600' : 'text-red-600';
    };

    const formatCurrency = (amount: number | undefined) => {
        if (!amount) return 'N/A';
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }).format(amount);
    };

    const formatDate = (dateString: string | undefined) => {
        if (!dateString) return 'N/A';
        return new Date(dateString).toLocaleString();
    };

    if (loading) {
        return (
            <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
                <h2 className='text-lg font-semibold text-gray-900 mb-4'>
                    Recent Trades
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
                    Recent Trades
                </h2>
                <div className='text-center py-8'>
                    <div className='text-red-600 mb-2'>{error}</div>
                    <button
                        onClick={fetchTrades}
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
                        Recent Trades
                    </h2>
                    <button
                        onClick={fetchTrades}
                        className='text-sm text-primary-600 hover:text-primary-700 font-medium'
                    >
                        Refresh
                    </button>
                </div>
            </div>

            <div className='overflow-x-auto'>
                {trades.length === 0 ? (
                    <div className='p-6 text-center text-gray-500'>
                        No trades available
                    </div>
                ) : (
                    <table className='min-w-full divide-y divide-gray-200'>
                        <thead className='bg-gray-50'>
                            <tr>
                                <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                                    Symbol
                                </th>
                                <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                                    Side
                                </th>
                                <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                                    Quantity
                                </th>
                                <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                                    Entry Price
                                </th>
                                <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                                    Status
                                </th>
                                <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                                    P&L
                                </th>
                                <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                                    Created
                                </th>
                            </tr>
                        </thead>
                        <tbody className='bg-white divide-y divide-gray-200'>
                            {trades.map((trade) => (
                                <tr key={trade.id} className='hover:bg-gray-50'>
                                    <td className='px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900'>
                                        {trade.symbol}
                                    </td>
                                    <td className='px-6 py-4 whitespace-nowrap text-sm'>
                                        <span
                                            className={`font-medium ${getSideColor(trade.side)}`}
                                        >
                                            {trade.side}
                                        </span>
                                    </td>
                                    <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-900'>
                                        {trade.quantity.toFixed(8)}
                                    </td>
                                    <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-900'>
                                        {formatCurrency(trade.entry_price)}
                                    </td>
                                    <td className='px-6 py-4 whitespace-nowrap'>
                                        <span
                                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                                                trade.status,
                                            )}`}
                                        >
                                            {trade.status}
                                        </span>
                                    </td>
                                    <td className='px-6 py-4 whitespace-nowrap text-sm'>
                                        <span
                                            className={`font-medium ${getPnlColor(trade.pnl)}`}
                                        >
                                            {formatCurrency(trade.pnl)}
                                        </span>
                                    </td>
                                    <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-500'>
                                        {formatDate(trade.created_at)}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
}
