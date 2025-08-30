import Link from 'next/link';

export default function NotFound() {
    return (
        <div className='flex min-h-screen items-center justify-center'>
            <div className='text-center'>
                <h2 className='text-6xl font-bold text-gray-900 mb-4'>404</h2>
                <h3 className='text-2xl font-semibold text-gray-700 mb-4'>
                    Page Not Found
                </h3>
                <p className='text-gray-600 mb-6'>
                    The page you're looking for doesn't exist.
                </p>
                <Link
                    href='/'
                    className='inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500'
                >
                    Go Home
                </Link>
            </div>
        </div>
    );
}
