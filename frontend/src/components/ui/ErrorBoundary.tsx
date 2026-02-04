'use client';

import { Component } from 'react';

export class ErrorBoundary extends Component<
    ErrorBoundaryProps,
    ErrorBoundaryState
> {
    constructor(props: ErrorBoundaryProps) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError(error: Error): ErrorBoundaryState {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: any) {
        console.error('Error caught by boundary:', error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                this.props.fallback || (
                    <div className='bg-red-50 border border-red-200 rounded-lg p-6 text-center'>
                        <div className='text-red-600 font-medium mb-2'>
                            Something went wrong
                        </div>
                        <div className='text-red-500 text-sm mb-4'>
                            {this.state.error?.message ||
                                'An unexpected error occurred'}
                        </div>
                        <button
                            onClick={() =>
                                this.setState({
                                    hasError: false,
                                    error: undefined,
                                })
                            }
                            className='text-primary-600 hover:text-primary-700 font-medium'
                        >
                            Try Again
                        </button>
                    </div>
                )
            );
        }

        return this.props.children;
    }
}
