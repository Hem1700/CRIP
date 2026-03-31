import { describe, it, expect, beforeEach } from 'vitest'
import { useThemeStore } from '../store/themeStore'

describe('themeStore', () => {
  beforeEach(() => {
    useThemeStore.setState({ theme: 'light' })
    localStorage.clear()
  })

  it('defaults to light theme', () => {
    expect(useThemeStore.getState().theme).toBe('light')
  })

  it('toggle switches light → dark', () => {
    useThemeStore.getState().toggle()
    expect(useThemeStore.getState().theme).toBe('dark')
  })

  it('toggle switches dark → light', () => {
    useThemeStore.setState({ theme: 'dark' })
    useThemeStore.getState().toggle()
    expect(useThemeStore.getState().theme).toBe('light')
  })
})
