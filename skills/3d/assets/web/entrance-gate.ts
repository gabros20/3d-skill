/**
 * entrance-gate.ts: the consumer side of the page's entrance signal. Copy and own.
 *
 * Owns: reading `data-entrance` (pending | running | tail | settled) on a scope element (default
 * `<html>`) and waiting for a phase through the bubbling `entrance:phase` event, with a failsafe
 * timeout. DOM only, no imports, SSR-safe.
 * Must not: start anything itself (callers decide what each phase unlocks:
 * references/threejs-orchestration.md), or publish a phase on a page that has a publisher. The
 * entrance's owner publishes (`scroll-animation`'s page lifecycle); trackEntranceAlone() below is
 * the stand-in for a page that has none.
 *
 * Contract: an absent attribute means "no entrance" and resolves 'none' at once. Phases only move
 * forward within a visit; `tail` may be skipped. An unknown value is treated as absent.
 *
 * Per visit: the owner restarts the phase for each client-side navigation (`pending` again, on
 * `<html>`, before the new route's effects run), so a scene mounted by that navigation reads the new
 * visit's phase, never the last page's `settled`. A wait that is still open when a visit begins
 * carries on into it.
 *
 * The timeout runs on the entrance's clock, not the caller's and not the navigation's. It counts
 * from where the entrance started: the owner's stamp (`data-entrance-started` on `<html>`,
 * performance.now() at `running`), else first contentful paint (a CSS entrance plays from there),
 * else navigation start. Counted from navigation start alone it includes the network and ends in
 * the middle of the entrance on a slow phone. While an owner holds the visit at `pending` (a route
 * transition, a loader) no timeout runs: the owner's own caps bound that wait. A caller with a clock
 * of its own passes `since`.
 */

export type EntrancePhase = 'pending' | 'running' | 'tail' | 'settled'
export type EntranceWait = 'phase' | 'none' | 'timeout'

export interface WhenEntranceOptions {
  /** The element carrying `data-entrance`. Default `document.documentElement`. */
  scope?: Element
  /**
   * Failsafe: resolve 'timeout' once `performance.now()` reaches the entrance's start plus
   * `timeoutMs`. Default 2500. `Infinity` waits for the phase.
   */
  timeoutMs?: number
  /**
   * The `performance.now()` the timeout counts from, when the caller knows better than the default
   * (the owner's stamp, else first contentful paint, else navigation start): a scope with its own
   * entrance passes the time it mounted.
   */
  since?: number
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
 * performance.now() at which the entrance on `scope` started, or null while an owner still holds
 * the visit at `pending` (its clock has not started). See the header.
 */
export function entranceStartedAt(scope?: Element): number | null {
  if (typeof document === 'undefined') return 0
  const html = document.documentElement
  if ((scope ?? html) === html) {
    const stamped = Number.parseFloat(html.getAttribute('data-entrance-started') ?? '')
    if (Number.isFinite(stamped)) return stamped
    if (html.getAttribute('data-visit') !== null && readEntrance(html) === 'pending') return null
  }
  const paint = typeof performance.getEntriesByName === 'function' ? performance.getEntriesByName('first-contentful-paint')[0] : undefined
  return paint ? paint.startTime : 0
}

/**
 * Resolves 'phase' once the scope's phase is at or past `phase`, 'none' when the attribute is
 * absent (now, or removed while waiting), 'timeout' once the entrance has run `timeoutMs` (at once,
 * on the next task, if it already has: a page past its load entrance never waits).
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

  const { timeoutMs = 2500, since } = opts
  return new Promise<EntranceWait>((resolve, reject) => {
    let timer: ReturnType<typeof setTimeout> | undefined
    let armedFor: number | null = null
    // Armed once the entrance has a start, and again if a new visit moves it.
    const arm = (): void => {
      if (!Number.isFinite(timeoutMs)) return
      const from = since ?? entranceStartedAt(scope)
      if (from === armedFor) return
      if (timer !== undefined) clearTimeout(timer)
      timer = undefined
      armedFor = from
      if (from === null) return
      timer = setTimeout(
        () => {
          cleanup()
          resolve('timeout')
        },
        Math.max(0, from + timeoutMs - performance.now()),
      )
    }
    const cleanup = (): void => {
      scope.removeEventListener('entrance:phase', onPhase)
      signal?.removeEventListener('abort', onAbort)
      if (timer !== undefined) clearTimeout(timer)
    }
    // The publisher writes the attribute before it dispatches, so the attribute is the truth.
    function onPhase(): void {
      const result = check()
      if (!result) return arm()
      cleanup()
      resolve(result)
    }
    function onAbort(): void {
      cleanup()
      reject(signal?.reason)
    }
    scope.addEventListener('entrance:phase', onPhase)
    signal?.addEventListener('abort', onAbort, { once: true })
    arm()
  })
}

/**
 * The publisher for a page with no entrance owner: the 3d skill used alone, beside a CSS entrance.
 * Call it once from a client effect with the element whose CSS or WAAPI animations are the
 * entrance. It writes `running` on `<html>`, then `settled` once every finite animation under
 * `root` has finished (two frames with none left), and returns its stop. It stands down, doing
 * nothing, when an owner is on the page (`data-visit` on `<html>`: `scroll-animation`'s lifecycle)
 * or the phase is already past `running`. No `tail`: SceneCanvas then reveals at `settled`.
 */
export function trackEntranceAlone(root: Element): () => void {
  const html = document.documentElement
  if (html.getAttribute('data-visit') !== null || rank(readEntrance(html)) > 1) return () => {}
  const publish = (phase: EntrancePhase): void => {
    if (html.getAttribute('data-visit') !== null || rank(readEntrance(html)) >= rank(phase)) return
    html.setAttribute('data-entrance', phase)
    html.dispatchEvent(new CustomEvent('entrance:phase', { bubbles: true, detail: { phase } }))
  }
  let live = true
  let frame = 0
  const finite = (): Animation[] =>
    root.getAnimations({ subtree: true }).filter((a) => {
      const end = a.effect?.getComputedTiming().endTime
      return a.playState === 'running' && a.timeline === document.timeline && typeof end === 'number' && Number.isFinite(end)
    })
  const check = (): void => {
    if (!live) return
    const running = finite()
    if (!running.length) return publish('settled')
    Promise.allSettled(running.map((a) => a.finished)).then(() => {
      frame = requestAnimationFrame(() => (frame = requestAnimationFrame(check)))
    })
  }
  publish('running')
  frame = requestAnimationFrame(() => (frame = requestAnimationFrame(check)))
  return () => {
    live = false
    cancelAnimationFrame(frame)
  }
}
