'use client';

import { useState, useCallback } from 'react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ReferenceLine,
} from 'recharts';
import { apiClient } from '@/lib/api';
import { formatCurrency, formatDate } from '@/lib/utils';
import { useRealTimeData } from '@/hooks/useRealTimeData';

export function PnLChart({ className = '', timeRange = '7d' }: PnLChartProps) {
    const [selectedTimeRange, setSelectedTimeRange] = useState(timeRange);

    const fetchPnLData = useCallback(async () => {
        // For now, we'll generate mock data based on trades
        // In a real implementation, this would be a dedicated API endpoint
        const trades = await apiClient.getTrades(1000);
        return generatePnLData(trades, selectedTimeRange);
    }, [selectedTimeRange]);

    const { data, loading, error, refresh } = useRealTimeData({
        fetchFunction: fetchPnLData,
        interval: 120000, // 2 minutes
    });

    const generatePnLData = (
        trades: Trade[],
        range: string,
    ): PnLDataPoint[] => {
        const now = new Date();
        const days =
            range === '24h'
                ? 1
                : range === '7d'
                  ? 7
                  : range === '30d'
                    ? 30
                    : 90;
        const startDate = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);

        // Filter trades within the time range
        const filteredTrades = trades.filter((trade) => {
            if (!trade.created_at) return false;
            const tradeDate = new Date(trade.created_at);
            return tradeDate >= startDate && tradeDate <= now;
        });

        // Sort trades by date
        filteredTrades.sort(
            (a, b) =>
                new Date(a.created_at!).getTime() -
                new Date(b.created_at!).getTime(),
        );

        // Generate data points
        const dataPoints: PnLDataPoint[] = [];
        let cumulativePnL = 0;
        let currentDate = new Date(startDate);
        let tradeIndex = 0;

        while (currentDate <= now) {
            const dateStr = currentDate.toISOString().split('T')[0];
            let dailyPnL = 0;
            let tradeCount = 0;

            // Process all trades for this day
            while (
                tradeIndex < filteredTrades.length &&
                filteredTrades[tradeIndex].created_at &&
                new Date(
                    filteredTrades[tradeIndex].created_at!,
                ).toDateString() === currentDate.toDateString()
            ) {
                const trade = filteredTrades[tradeIndex];
                if (trade.pnl) {
                    dailyPnL += trade.pnl;
                    cumulativePnL += trade.pnl;
                    tradeCount++;
                }
                tradeIndex++;
            }

            dataPoints.push({
                timestamp: currentDate.toISOString(),
                cumulative_pnl: cumulativePnL,
                daily_pnl: dailyPnL,
                trade_count: tradeCount,
                date: dateStr,
            });

            // Move to next day (or hour for 24h view)
            if (range === '24h') {
                currentDate.setHours(currentDate.getHours() + 1);
            } else {
                currentDate.setDate(currentDate.getDate() + 1);
            }
        }

        return dataPoints;
    };

    const formatXAxisTick = (tickItem: string) => {
        const date = new Date(tickItem);
        if (selectedTimeRange === '24h') {
            return date.toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
            });
        } else {
            return date.toLocaleDateString([], {
                month: 'short',
                day: 'numeric',
            });
        }
    };

    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            return (
                <div className='bg-white p-3 border border-gray-200 rounded-lg shadow-lg'>
                    <p className='text-sm text-gray-600 mb-1'>
                        {selectedTimeRange === '24h'
                            ? new Date(label).toLocaleString()
                            : formatDate(label)}
                    </p>
                    <p className='text-sm font-medium'>
                        <span className='text-gray-700'>Cumulative P&L: </span>
                        <span
                            className={
                                data.cumulative_pnl >= 0
                                    ? 'text-green-600'
                                    : 'text-red-600'
                            }
                        >
                            {formatCurrency(data.cumulative_pnl)}
                        </span>
                    </p>
                    {data.daily_pnl !== 0 && (
                        <p className='text-sm'>
                            <span className='text-gray-700'>Daily P&L: </span>
                            <span
                                className={
                                    data.daily_pnl >= 0
                                        ? 'text-green-600'
                                        : 'text-red-600'
                                }
                            >
                                {formatCurrency(data.daily_pnl)}
                            </span>
                        </p>
                    )}
                    {data.trade_count > 0 && (
                        <p className='text-sm text-gray-600'>
                            Trades: {data.trade_count}
                        </p>
                    )}
                </div>
            );
        }
        return null;
    };

    const timeRangeOptions = [
        { value: '24h', label: '24H' },
        { value: '7d', label: '7D' },
        { value: '30d', label: '30D' },
        { value: '90d', label: '90D' },
    ];

    if (loading) {
        return (
            <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
                <div className='flex items-center justify-between mb-4'>
                    <h2 className='text-lg font-semibold text-gray-900'>
                        P&L Over Time
                    </h2>
                    <div className='flex space-x-1'>
                        {timeRangeOptions.map((option) => (
                            <div
                                key={option.value}
                                className='w-12 h-8 bg-gray-200 rounded animate-pulse'
                            />
                        ))}
                    </div>
                </div>
                <div className='h-80 bg-gray-100 rounded animate-pulse' />
            </div>
        );
    }

    if (error) {
        return (
            <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
                <h2 className='text-lg font-semibold text-gray-900 mb-4'>
                    P&L Over Time
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

    const latestPnL =
        data && data.length > 0 ? data[data.length - 1].cumulative_pnl : 0;

    return (
        <div className={`bg-white rounded-lg shadow ${className}`}>
            <div className='p-4 sm:p-6 border-b border-gray-200'>
                <div className='flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4'>
                    <div>
                        <h2 className='text-lg font-semibold text-gray-900'>
                            P&L Over Time
                        </h2>
                        <p
                            className={`text-2xl font-bold mt-1 ${latestPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}
                        >
                            {formatCurrency(latestPnL)}
                        </p>
                    </div>

                    <div className='flex space-x-1 bg-gray-100 rounded-lg p-1'>
                        {timeRangeOptions.map((option) => (
                            <button
                                key={option.value}
                                onClick={() =>
                                    setSelectedTimeRange(option.value as any)
                                }
                                className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                                    selectedTimeRange === option.value
                                        ? 'bg-white text-blue-600 shadow-sm'
                                        : 'text-gray-600 hover:text-gray-900'
                                }`}
                            >
                                {option.label}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            <div className='p-4 sm:p-6'>
                {!data || data.length === 0 ? (
                    <div className='text-center py-8 text-gray-500'>
                        No P&L data available for the selected time range
                    </div>
                ) : (
                    <div className='h-80'>
                        <ResponsiveContainer width='100%' height='100%'>
                            <LineChart
                                data={data}
                                margin={{
                                    top: 5,
                                    right: 30,
                                    left: 20,
                                    bottom: 5,
                                }}
                            >
                                <CartesianGrid
                                    strokeDasharray='3 3'
                                    stroke='#f0f0f0'
                                />
                                <XAxis
                                    dataKey='timestamp'
                                    tickFormatter={formatXAxisTick}
                                    stroke='#6b7280'
                                    fontSize={12}
                                />
                                <YAxis
                                    tickFormatter={(value) =>
                                        formatCurrency(value, true)
                                    }
                                    stroke='#6b7280'
                                    fontSize={12}
                                />
                                <Tooltip content={<CustomTooltip />} />
                                <ReferenceLine
                                    y={0}
                                    stroke='#6b7280'
                                    strokeDasharray='2 2'
                                />
                                <Line
                                    type='monotone'
                                    dataKey='cumulative_pnl'
                                    stroke='#3b82f6'
                                    strokeWidth={2}
                                    dot={false}
                                    activeDot={{ r: 4, fill: '#3b82f6' }}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                )}
            </div>
        </div>
    );
}
