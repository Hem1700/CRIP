import { clsx } from 'clsx'
import type { HTMLAttributes } from 'react'

export function Card({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={clsx(
        'rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4 shadow-sm',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}
