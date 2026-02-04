import { useState, useEffect, useCallback, useRef } from 'react';

export function useRealTimeData<T>({
    fetchFunction,
    interval = 30000,
    enabled = true,
}: UseRealTimeDataOptions<T>) {
    const [data, setData] = useState<T | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
    const intervalRef = useRef<NodeJS.Timeout | null>(null);

    const fetchData = useCallback(async () => {
        try {
            setError(null);
            const result = await fetchFunction();
            setData(result);
            setLastUpdated(new Date());
        } catch (err) {
            setError(
                err instanceof Error ? err.message : 'Failed to fetch data',
            );
            console.error('Error fetching real-time data:', err);
        } finally {
            setLoading(false);
        }
    }, [fetchFunction]);

    const refresh = useCallback(() => {
        fetchData();
    }, [fetchData]);

    useEffect(() => {
        if (!enabled) return;

        // Initial fetch
        fetchData();

        // Start polling
        intervalRef.current = setInterval(fetchData, interval);

        // Cleanup on unmount
        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
            }
        };
    }, [fetchData, interval, enabled]);

    // Pause/resume polling when tab visibility changes
    useEffect(() => {
        const handleVisibilityChange = () => {
            if (!enabled) return;

            if (document.hidden) {
                if (intervalRef.current) {
                    clearInterval(intervalRef.current);
                }
            } else {
                if (intervalRef.current) {
                    clearInterval(intervalRef.current);
                }
                intervalRef.current = setInterval(fetchData, interval);
            }
        };

        document.addEventListener('visibilitychange', handleVisibilityChange);

        return () => {
            document.removeEventListener(
                'visibilitychange',
                handleVisibilityChange,
            );
        };
    }, [fetchData, interval, enabled]);

    return {
        data,
        loading,
        error,
        lastUpdated,
        refresh,
    };
}
