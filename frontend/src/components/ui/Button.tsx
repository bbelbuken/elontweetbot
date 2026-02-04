import { forwardRef } from 'react';
import { cn } from '@/lib/utils';

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
    ({ className, variant = 'primary', size = 'md', ...props }, ref) => {
        return (
            <button
                className={cn(
                    'inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
                    {
                        'bg-primary-600 text-white hover:bg-primary-700 focus-visible:ring-primary-500':
                            variant === 'primary',
                        'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 focus-visible:ring-primary-500':
                            variant === 'secondary',
                        'bg-danger-600 text-white hover:bg-danger-700 focus-visible:ring-danger-500':
                            variant === 'danger',
                        'h-8 px-3 text-sm': size === 'sm',
                        'h-10 px-4 text-sm': size === 'md',
                        'h-12 px-6 text-base': size === 'lg',
                    },
                    className,
                )}
                ref={ref}
                {...props}
            />
        );
    },
);

Button.displayName = 'Button';

export { Button };
