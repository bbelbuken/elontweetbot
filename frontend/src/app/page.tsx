import Link from 'next/link';

export default function HomePage() {
    return (
        <div className='flex min-h-screen items-center justify-center'>
            <div className='text-center'>
                <h1 className='text-4xl font-bold text-gray-900 mb-4'>
                    Tweet Crypto Trading Bot
                </h1>
                <p className='text-lg text-gray-600 mb-8'>
                    AI-powered cryptocurrency trading driven by social media
                    sentiment
                </p>
                <Link
                    href='/dashboard'
                    className='inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500'
                >
                    Go to Dashboard
                </Link>
            </div>
        </div>
    );
}
