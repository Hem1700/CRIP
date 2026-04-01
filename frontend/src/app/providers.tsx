import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useLayoutEffect, type ReactNode } from 'react'
import { useThemeStore } from '../store/themeStore'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1 },
  },
})

function ThemeApplier() {
  const theme = useThemeStore((s) => s.theme)
  useLayoutEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [theme])
  return null
}

export function Providers({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeApplier />
      {children}
    </QueryClientProvider>
  )
}
