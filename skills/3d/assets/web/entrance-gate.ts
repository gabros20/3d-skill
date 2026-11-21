/**
 * entrance-gate.ts: the consumer side of the page-load entrance signal. Copy and own.
 *
 * Owns: reading `data-entrance` (pending | running | tail | settled) on a scope element (default
 * `<html>`) and waiting for a phase through the bubbling `entrance:phase` event, with a failsafe
 * timeout. DOM only, no imports, SSR-safe.
 * Must not: publish a phase (the entrance's owner does: `scroll-animation`'s `entrance-signal.ts`),
 * or start anything itself. Callers decide what each phase unlocks (references/threejs-orchestration.md).
 *
 * Contract: an absent attribute means "no entrance" and resolves 'none' at once. Phases only move
 * forward; `tail` may be skipped. An unknown value is treated as absent.
 */

export type EntrancePhase = 'pending' | 'running' | 'tail' | 'settled'
export type EntranceWait = 'phase' | 'none' | 'timeout'

export interface WhenEntranceOptions {
  /** The element carrying `data-entrance`. Default `document.documentElement`. */
  scope?: Element
  /** Failsafe: resolve 'timeout' after this many ms. Default 2500. `Infinity` waits for the phase. */
  timeoutMs?: number
  /** Abort rejects with `signal.reason` and removes the listener and timer. */
  signal?: AbortSignal
}

const ORDER: readonly EntrancePhase[] = ['pending', 'running', 'tail', 'settled']
const rank = (phase: string | null): number => (phase === null ? -1 : ORDER.indexOf(phase as EntrancePhase))

/** The current phase on `scope`, or null when the page has no entrance (or no document). */
export function readEntrance(scope?: Element): EntrancePhase | null {
  if (typeof document === 'undefined') return null
  const el = scope ?? document.documentElement
  const value = el.getAttribute('data-entrance')
  return rank(value) >= 0 ? (value as EntrancePhase) : null
}

/**
 * Resolves 'phase' once the scope's phase is at or past `phase`, 'none' when the attribute is
 * absent (now, or removed while waiting), 'timeout' after `timeoutMs`.
 */
export function whenEntrance(
  phase: 'running' | 'tail' | 'settled',
  opts: WhenEntranceOptions = {},
): Promise<EntranceWait> {
  if (typeof document === 'undefined') return Promise.resolve('none')
  const { signal } = opts
  if (signal?.aborted) return Promise.reject(signal.reason)
  const scope = opts.scope ?? document.documentElement
  const target = rank(phase)
  const check = (): EntranceWait | null => {
    const now = readEntrance(scope)
    if (now === null) return 'none'
    return rank(now) >= target ? 'phase' : null
  }
  const immediate = check()
  if (immediate) return Promise.resolve(immediate)

  const timeoutMs = opts.timeoutMs ?? 2500
  return new Promise<EntranceWait>((resolve, reject) => {
    let timer: ReturnType<typeof setTimeout> | undefined
    const cleanup = (): void => {
      scope.removeEventListener('entrance:phase', onPhase)
      signal?.removeEventListener('abort', onAbort)
      if (timer !== undefined) clearTimeout(timer)
    }
    // The publisher writes the attribute before it dispatches, so the attribute is the truth.
    function onPhase(): void {
      const result = check()
      if (!result) return
      cleanup()
      resolve(result)
    }
    function onAbort(): void {
      cleanup()
      reject(signal?.reason)
    }
    scope.addEventListener('entrance:phase', onPhase)
    signal?.addEventListener('abort', onAbort, { once: true })
    if (Number.isFinite(timeoutMs)) {
      timer = setTimeout(() => {
        cleanup()
        resolve('timeout')
      }, Math.max(0, timeoutMs))
    }
  })
}
