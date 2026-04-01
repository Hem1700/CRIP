import { cva, type VariantProps } from 'class-variance-authority'
import { type ButtonHTMLAttributes } from 'react'
import { clsx } from 'clsx'

const button = cva(
  'inline-flex items-center justify-center rounded font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none',
  {
    variants: {
      variant: {
        primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
        secondary: 'bg-gray-100 text-gray-900 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-100 dark:hover:bg-gray-700 focus:ring-gray-400',
        ghost: 'text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-white dark:hover:bg-gray-800 focus:ring-gray-400',
      },
      size: {
        sm: 'text-xs px-2.5 py-1',
        md: 'text-sm px-3 py-1.5',
        lg: 'text-sm px-4 py-2',
      },
    },
    defaultVariants: { variant: 'primary', size: 'md' },
  }
)

interface Props extends ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof button> {}

export function Button({ variant, size, className, ...props }: Props) {
  return <button className={clsx(button({ variant, size }), className)} {...props} />
}
