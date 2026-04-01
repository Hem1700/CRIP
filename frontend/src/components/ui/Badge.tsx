import { clsx } from 'clsx'

const COLOR_MAP: Record<string, string> = {
  red: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  orange: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
  yellow: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
  green: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  blue: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  gray: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400',
}

interface Props {
  color?: string
  children: React.ReactNode
  className?: string
}

export function Badge({ color = 'gray', children, className }: Props) {
  return (
    <span className={clsx('inline-flex items-center px-2 py-0.5 rounded text-xs font-medium', COLOR_MAP[color] ?? COLOR_MAP['gray'], className)}>
      {children}
    </span>
  )
}
