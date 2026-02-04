// Global type definitions for the Tweet Crypto Trading Bot

// =============================================================================
// CORE DATA MODELS - Used across backend API and database
// =============================================================================

interface Tweet {
    id: number;
    author: string;
    text: string;
    created_at: string;
    sentiment_score?: number;
    signal_score?: number;
    processed: boolean;
}

interface Trade {
    id?: number;
    tweet_id: number;
    symbol: string;
    side: 'LONG' | 'SHORT';
    leverage: number;
    quantity: number;
    entry_price?: number;
    stop_loss?: number;
    take_profit?: number;
    status: 'OPEN' | 'CLOSED' | 'CANCELLED';
    pnl?: number;
    created_at?: string;
    closed_at?: string;
}

interface Position {
    id?: number;
    symbol: string;
    size: number;
    avg_entry: number;
    leverage: number;
    unrealized_pnl?: number;
    updated_at?: string;
}

interface SystemMetrics {
    tweets_processed: number;
    trades_executed: number;
    current_pnl: number;
    daily_pnl: number;
    open_positions: number;
    system_status: 'healthy' | 'unhealthy';
}

interface HealthCheck {
    status: 'healthy' | 'unhealthy';
    checks: {
        database: boolean;
        redis: boolean;
        twitter_api: boolean;
        binance_api: boolean;
    };
}

// =============================================================================
// API COMMUNICATION - Used in lib/api.ts
// =============================================================================

interface ApiResponse<T> {
    data: T;
    success: boolean;
    message?: string;
}

interface TweetWithSignal extends Tweet {
    signal_score: number;
    sentiment_score: number;
}

interface DashboardData {
    recent_tweets: TweetWithSignal[];
    current_positions: Position[];
    recent_trades: Trade[];
    metrics: SystemMetrics;
}

// =============================================================================
// COMPONENT PROPS - Used in React components
// =============================================================================

// TweetFeed.tsx component props
interface TweetFeedProps {
    className?: string;
}

// PositionsOverview.tsx component props
interface PositionsOverviewProps {
    className?: string;
}

// MetricsOverview.tsx component props
interface MetricsOverviewProps {
    className?: string;
}

// TradeHistory.tsx component props
interface TradeHistoryProps {
    className?: string;
    limit?: number;
}

// PnLChart.tsx component props
interface PnLChartProps {
    className?: string;
    timeRange?: '24h' | '7d' | '30d' | '90d';
}

// PnL data structure for charts
interface PnLDataPoint {
    timestamp: string;
    cumulative_pnl: number;
    daily_pnl: number;
    trade_count: number;
    date: string;
}

// =============================================================================
// HOOKS - Used in custom hooks
// =============================================================================

// useRealTimeData hook options
interface UseRealTimeDataOptions<T> {
    fetchFunction: () => Promise<T>;
    interval?: number;
    enabled?: boolean;
}

// =============================================================================
// UI COMPONENTS - Used in ui/ components
// =============================================================================

// Button.tsx component props
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'danger';
    size?: 'sm' | 'md' | 'lg';
}

// LoadingSpinner.tsx component props
interface LoadingSpinnerProps {
    size?: 'sm' | 'md' | 'lg';
    className?: string;
}

// ErrorBoundary.tsx component props
interface ErrorBoundaryProps {
    children: React.ReactNode;
    fallback?: React.ReactNode;
}

interface ErrorBoundaryState {
    hasError: boolean;
    error?: Error;
}
