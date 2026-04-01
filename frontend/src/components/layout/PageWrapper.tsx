import type { ReactNode } from 'react'

export function PageWrapper({ children }: { children: ReactNode }) {
  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
      {children}
    </main>
  )
}
