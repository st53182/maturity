import { onMounted, onUnmounted } from 'vue'

export function useDashboardShortcuts(opts: {
  focusSearch: () => void
  onEsc: () => void
  onHelp: () => void
  enabled?: () => boolean
}) {
  function onKey(e: KeyboardEvent) {
    if (opts.enabled && !opts.enabled()) return
    const t = e.target as HTMLElement
    if (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT' || t.isContentEditable) {
      if (e.key === 'Escape') opts.onEsc()
      return
    }
    if (e.key === '/') {
      e.preventDefault()
      opts.focusSearch()
    }
    if (e.key === 'Escape') opts.onEsc()
    if (e.key === '?') {
      e.preventDefault()
      opts.onHelp()
    }
  }

  onMounted(() => window.addEventListener('keydown', onKey))
  onUnmounted(() => window.removeEventListener('keydown', onKey))
}
