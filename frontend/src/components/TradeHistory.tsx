import { useState, useMemo, useCallback } from 'react';
import { apiClient } from '@/lib/api';
import { formatCurrency, formatDate, getPnlColor } from '@/lib/utils';
import { useRealTimeData } from '@/hooks/useRealTimeData';

export function TradeHistory({
    className = '',
    limit = 10,
}: TradeHistoryProps) {
    const [sortField, setSortField] = useState<keyof Trade>('created_at');
    const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
    const [filterStatus, setFilterStatus] = useState<string>('all');
    const [filterSymbol, setFilterSymbol] = useState<string>('all');
    const [searchTerm, setSearchTerm] = useState<string>('');

    const fetchTrades = useCallback(async () => {
        return await apiClient.getTrades(limit);
    }, [limit]);

    const {
        data: trades,
        loading,
        error,
        refresh,
    } = useRealTimeData({
        fetchFunction: fetchTrades,
        interval: 30000, // 30 seconds
    });

    // Get unique symbols and statuses for filters
    const uniqueSymbols = useMemo(() => {
        if (!trades) return [];
        const symbols = Array.from(
            new Set(trades.map((trade) => trade.symbol)),
        );
        return symbols.sort();
    }, [trades]);

    const uniqueStatuses = useMemo(() => {
        if (!trades) return [];
        const statuses = Array.from(
            new Set(trades.map((trade) => trade.status)),
        );
        return statuses.sort();
    }, [trades]);

    // Filter and sort trades
    const filteredAndSortedTrades = useMemo(() => {
        if (!trades) return [];

        let filtered = trades.filter((trade) => {
            const matchesStatus =
                filterStatus === 'all' || trade.status === filterStatus;
            const matchesSymbol =
                filterSymbol === 'all' || trade.symbol === filterSymbol;
            const matchesSearch =
                searchTerm === '' ||
                trade.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
                trade.side.toLowerCase().includes(searchTerm.toLowerCase());

            return matchesStatus && matchesSymbol && matchesSearch;
        });

        // Sort trades
        filtered.sort((a, b) => {
            const aValue = a[sortField];
            const bValue = b[sortField];

            if (aValue === undefined || aValue === null) return 1;
            if (bValue === undefined || bValue === null) return -1;

            let comparison = 0;
            if (typeof aValue === 'string' && typeof bValue === 'string') {
                comparison = aValue.localeCompare(bValue);
            } else if (
                typeof aValue === 'number' &&
                typeof bValue === 'number'
            ) {
                comparison = aValue - bValue;
            } else {
                comparison = String(aValue).localeCompare(String(bValue));
            }

            return sortDirection === 'asc' ? comparison : -comparison;
        });

        return filtered;
    }, [
        trades,
        sortField,
        sortDirection,
        filterStatus,
        filterSymbol,
        searchTerm,
    ]);

    const handleSort = (field: keyof Trade) => {
        if (sortField === field) {
            setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
        } else {
            setSortField(field);
            setSortDirection('desc');
        }
    };

    const getSortIcon = (field: keyof Trade) => {
        if (sortField !== field) {
            return (
                <svg
                    className='w-4 h-4 text-gray-400'
                    fill='none'
                    stroke='currentColor'
                    viewBox='0 0 24 24'
                >
                    <path
                        strokeLinecap='round'
                        strokeLinejoin='round'
                        strokeWidth={2}
                        d='M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4'
                    />
                </svg>
            );
        }

        return sortDirection === 'asc' ? (
            <svg
                className='w-4 h-4 text-blue-500'
                fill='none'
                stroke='currentColor'
                viewBox='0 0 24 24'
            >
                <path
                    strokeLinecap='round'
                    strokeLinejoin='round'
                    strokeWidth={2}
                    d='M5 15l7-7 7 7'
                />
            </svg>
        ) : (
            <svg
                className='w-4 h-4 text-blue-500'
                fill='none'
                stroke='currentColor'
                viewBox='0 0 24 24'
            >
                <path
                    strokeLinecap='round'
                    strokeLinejoin='round'
                    strokeWidth={2}
                    d='M19 9l-7 7-7-7'
                />
            </svg>
        );
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
            <div className='p-4 sm:p-6 border-b border-gray-200'>
                <div className='flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4'>
                    <h2 className='text-lg font-semibold text-gray-900'>
                        Trade History ({filteredAndSortedTrades.length})
                    </h2>

                    {/* Filters and Search */}
                    <div className='flex flex-col sm:flex-row gap-2 sm:gap-4'>
                        {/* Search */}
                        <div className='relative'>
                            <input
                                type='text'
                                placeholder='Search trades...'
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className='w-full sm:w-48 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
                            />
                            <svg
                                className='absolute right-3 top-2.5 h-4 w-4 text-gray-400'
                                fill='none'
                                stroke='currentColor'
                                viewBox='0 0 24 24'
                            >
                                <path
                                    strokeLinecap='round'
                                    strokeLinejoin='round'
                                    strokeWidth={2}
                                    d='M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z'
                                />
                            </svg>
                        </div>

                        {/* Status Filter */}
                        <select
                            value={filterStatus}
                            onChange={(e) => setFilterStatus(e.target.value)}
                            className='px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
                        >
                            <option value='all'>All Status</option>
                            {uniqueStatuses.map((status) => (
                                <option key={status} value={status}>
                                    {status}
                                </option>
                            ))}
                        </select>

                        {/* Symbol Filter */}
                        <select
                            value={filterSymbol}
                            onChange={(e) => setFilterSymbol(e.target.value)}
                            className='px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
                        >
                            <option value='all'>All Symbols</option>
                            {uniqueSymbols.map((symbol) => (
                                <option key={symbol} value={symbol}>
                                    {symbol}
                                </option>
                            ))}
                        </select>

                        {/* Refresh Button */}
                        <button
                            onClick={refresh}
                            className='px-3 py-2 text-sm text-blue-600 hover:text-blue-700 font-medium border border-blue-200 rounded-md hover:bg-blue-50 transition-colors'
                        >
                            Refresh
                        </button>
                    </div>
                </div>
            </div>

            <div className='overflow-x-auto'>
                {filteredAndSortedTrades.length === 0 ? (
                    <div className='p-6 text-center text-gray-500'>
                        {!trades || trades.length === 0
                            ? 'No trades available'
                            : 'No trades match your filters'}
                    </div>
                ) : (
                    <table className='min-w-full divide-y divide-gray-200'>
                        <thead className='bg-gray-50'>
                            <tr>
                                <th
                                    className='px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors'
                                    onClick={() => handleSort('symbol')}
                                >
                                    <div className='flex items-center space-x-1'>
                                        <span>Symbol</span>
                                        {getSortIcon('symbol')}
                                    </div>
                                </th>
                                <th
                                    className='px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors'
                                    onClick={() => handleSort('side')}
                                >
                                    <div className='flex items-center space-x-1'>
                                        <span>Side</span>
                                        {getSortIcon('side')}
                                    </div>
                                </th>
                                <th
                                    className='px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors'
                                    onClick={() => handleSort('quantity')}
                                >
                                    <div className='flex items-center space-x-1'>
                                        <span className='hidden sm:inline'>
                                            Quantity
                                        </span>
                                        <span className='sm:hidden'>Qty</span>
                                        {getSortIcon('quantity')}
                                    </div>
                                </th>
                                <th
                                    className='px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors'
                                    onClick={() => handleSort('entry_price')}
                                >
                                    <div className='flex items-center space-x-1'>
                                        <span className='hidden sm:inline'>
                                            Entry Price
                                        </span>
                                        <span className='sm:hidden'>Price</span>
                                        {getSortIcon('entry_price')}
                                    </div>
                                </th>
                                <th
                                    className='px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors'
                                    onClick={() => handleSort('status')}
                                >
                                    <div className='flex items-center space-x-1'>
                                        <span>Status</span>
                                        {getSortIcon('status')}
                                    </div>
                                </th>
                                <th
                                    className='px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors'
                                    onClick={() => handleSort('pnl')}
                                >
                                    <div className='flex items-center space-x-1'>
                                        <span>P&L</span>
                                        {getSortIcon('pnl')}
                                    </div>
                                </th>
                                <th
                                    className='px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors'
                                    onClick={() => handleSort('created_at')}
                                >
                                    <div className='flex items-center space-x-1'>
                                        <span className='hidden sm:inline'>
                                            Created
                                        </span>
                                        <span className='sm:hidden'>Date</span>
                                        {getSortIcon('created_at')}
                                    </div>
                                </th>
                            </tr>
                        </thead>
                        <tbody className='bg-white divide-y divide-gray-200'>
                            {filteredAndSortedTrades.map((trade) => (
                                <tr
                                    key={trade.id}
                                    className='hover:bg-gray-50 transition-colors'
                                >
                                    <td className='px-3 sm:px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900'>
                                        {trade.symbol}
                                    </td>
                                    <td className='px-3 sm:px-6 py-4 whitespace-nowrap text-sm'>
                                        <span
                                            className={`font-medium ${getSideColor(trade.side)}`}
                                        >
                                            {trade.side}
                                        </span>
                                    </td>
                                    <td className='px-3 sm:px-6 py-4 whitespace-nowrap text-sm text-gray-900'>
                                        <span className='hidden sm:inline'>
                                            {trade.quantity.toFixed(8)}
                                        </span>
                                        <span className='sm:hidden'>
                                            {trade.quantity.toFixed(4)}
                                        </span>
                                    </td>
                                    <td className='px-3 sm:px-6 py-4 whitespace-nowrap text-sm text-gray-900'>
                                        {trade.entry_price
                                            ? formatCurrency(trade.entry_price)
                                            : 'N/A'}
                                    </td>
                                    <td className='px-3 sm:px-6 py-4 whitespace-nowrap'>
                                        <span
                                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                                                trade.status,
                                            )}`}
                                        >
                                            {trade.status}
                                        </span>
                                    </td>
                                    <td className='px-3 sm:px-6 py-4 whitespace-nowrap text-sm'>
                                        <span
                                            className={`font-medium ${getPnlColor(trade.pnl || 0)}`}
                                        >
                                            {trade.pnl
                                                ? formatCurrency(trade.pnl)
                                                : 'N/A'}
                                        </span>
                                    </td>
                                    <td className='px-3 sm:px-6 py-4 whitespace-nowrap text-sm text-gray-500'>
                                        <span className='hidden sm:inline'>
                                            {trade.created_at
                                                ? formatDate(trade.created_at)
                                                : 'N/A'}
                                        </span>
                                        <span className='sm:hidden'>
                                            {trade.created_at
                                                ? new Date(
                                                      trade.created_at,
                                                  ).toLocaleDateString()
                                                : 'N/A'}
                                        </span>
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
