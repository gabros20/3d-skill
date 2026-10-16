/**
 * adapters/native.ts: feeds the conductor from native window scroll over one range wrapper.
 *
 * Owns: measuring the wrapper, exact progress, re-measure triggers, rehydrate on resume.
 * Must not: create the pin or the `lvh` margins (scroll-animation owns them; without it see
 * references/scroll-adapters.md), smooth anything, or read geometry on every scroll event.
 *
 * Progress = (scrollY - wrapperTop) / (wrapperHeight - lvh). The wrapper is measured, never the pin
 * (a sticky element stops moving). Run it under native scroll or Lenis; under ScrollSmoother use
 * adapters/gsap.ts.
 */
import type { ConductorInput, ScrollAdapter } from '../conductor'

export interface NativeAdapterOptions {
  /** The range wrapper that contains the sticky pin and the content layer. */
  wrapper: HTMLElement
}

export function attachNativeScroll(conductor: ConductorInput, options: NativeAdapterOptions): ScrollAdapter {
  const { wrapper } = options

  // 100lvh probe: the pin is sized in lvh, so the range is measured against lvh, not innerHeight
  // (innerHeight moves with the iOS toolbar and would shift progress mid-scroll).
  const probe = document.createElement('div')
  probe.setAttribute('aria-hidden', 'true')
  probe.style.cssText =
    'position:fixed;top:0;left:0;width:0;height:100lvh;visibility:hidden;pointer-events:none'
  document.body.appendChild(probe)

  let top = 0
  let range = 1
  let lastWidth = window.innerWidth
  let measureFrame = 0

  const measure = (): void => {
    const rect = wrapper.getBoundingClientRect()
    const lvh = probe.getBoundingClientRect().height || window.innerHeight
    top = rect.top + window.scrollY
    range = Math.max(rect.height - lvh, 1)
  }

  const update = (): void => {
    conductor.setExact((window.scrollY - top) / range)
  }

  const refresh = (): void => {
    measure()
    update()
  }

  // One rAF deferral, coalesced: Safari can fire resize while layout still holds the old size.
  const scheduleMeasure = (): void => {
    if (measureFrame) return
    measureFrame = requestAnimationFrame(() => {
      measureFrame = 0
      refresh()
    })
  }

  const onResize = (): void => {
    const coarse = window.matchMedia('(pointer: coarse)').matches
    const widthChanged = window.innerWidth !== lastWidth
    lastWidth = window.innerWidth
    // A height-only resize on touch is the toolbar showing or hiding, not a layout change.
    if (coarse && !widthChanged) return
    scheduleMeasure()
  }

  const rehydrate = (): void => {
    refresh()
    conductor.settle()
  }
  const onPageShow = (): void => rehydrate()
  const onVisibility = (): void => {
    if (!document.hidden) rehydrate()
  }

  const resizeObserver = new ResizeObserver(scheduleMeasure)
  resizeObserver.observe(wrapper)
  window.addEventListener('scroll', update, { passive: true })
  window.addEventListener('resize', onResize)
  window.addEventListener('pageshow', onPageShow)
  window.addEventListener('hashchange', rehydrate)
  window.addEventListener('focus', rehydrate)
  document.addEventListener('visibilitychange', onVisibility)
  void document.fonts?.ready.then(scheduleMeasure)

  rehydrate()

  return {
    refresh,
    destroy() {
      if (measureFrame) cancelAnimationFrame(measureFrame)
      resizeObserver.disconnect()
      window.removeEventListener('scroll', update)
      window.removeEventListener('resize', onResize)
      window.removeEventListener('pageshow', onPageShow)
      window.removeEventListener('hashchange', rehydrate)
      window.removeEventListener('focus', rehydrate)
      document.removeEventListener('visibilitychange', onVisibility)
      probe.remove()
    },
  }
}
