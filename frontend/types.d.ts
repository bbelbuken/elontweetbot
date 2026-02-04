// Global type definitions for the Tweet Crypto Trading Bot

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
