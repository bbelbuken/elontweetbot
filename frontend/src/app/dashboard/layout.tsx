import { Metadata } from 'next';

export const metadata: Metadata = {
    title: 'Dashboard - Tweet Crypto Trading Bot',
    description:
        'Real-time trading dashboard with sentiment analysis and portfolio tracking',
};

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className='min-h-screen bg-gray-50'>
            <nav className='bg-white shadow-sm border-b border-gray-200'>
                <div className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8'>
                    <div className='flex justify-between h-16'>
                        <div className='flex items-center'>
                            <h1 className='text-xl font-semibold text-gray-900'>
                                Trading Bot Dashboard
                            </h1>
                        </div>
                        <div className='flex items-center space-x-4'>
                            <span className='text-sm text-gray-500'>
                                Status:{' '}
                                <span className='text-green-600 font-medium'>
                                    Active
                                </span>
                            </span>
                        </div>
                    </div>
                </div>
            </nav>
            <main className='max-w-7xl mx-auto py-6 sm:px-6 lg:px-8'>
                {children}
            </main>
        </div>
    );
}
