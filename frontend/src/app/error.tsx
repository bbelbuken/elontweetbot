'use client';

import { useEffect } from 'react';

export default function Error({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        console.error(error);
    }, [error]);

    return (
        <div className='flex min-h-screen items-center justify-center'>
            <div className='text-center'>
                <h2 className='text-2xl font-bold text-gray-900 mb-4'>
                    Something went wrong!
                </h2>
                <p className='text-gray-600 mb-6'>
                    An error occurred while loading the application.
                </p>
                <button
                    onClick={reset}
                    className='inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500'
                >
                    Try again
                </button>
            </div>
        </div>
    );
}
