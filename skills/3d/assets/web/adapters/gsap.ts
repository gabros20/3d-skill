/**
 * adapters/gsap.ts: feeds the conductor from GSAP ScrollTrigger and ticks it from gsap.ticker.
 *
 * Owns: one non-scrubbed ScrollTrigger over the range wrapper, one ticker callback.
 * Must not: set `scrub` on the trigger that feeds the conductor (the conductor is the smoother),
 * nest the scene in a GSAP `pin: true`, run with a second scroll authority, or add a lerp on top.
 * Under Lenis, wire the one tick first (see references/scroll-adapters.md), then call these.
 */
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import type { Conductor, ConductorInput, ScrollAdapter, StateListener } from '../conductor'

export interface GsapAdapterOptions {
  /** The range wrapper (not the sticky pin). */
  wrapper: Element
  /** An iOS toolbar show/hide fires resize without a layout change. Default true. */
  ignoreMobileResize?: boolean
}

export function attachScrollTrigger(conductor: ConductorInput, options: GsapAdapterOptions): ScrollAdapter {
  gsap.registerPlugin(ScrollTrigger)
  if (options.ignoreMobileResize !== false) ScrollTrigger.config({ ignoreMobileResize: true })

  const trigger = ScrollTrigger.create({
    trigger: options.wrapper,
    start: 'top top',
    end: 'bottom bottom',
    // No `scrub`, no `pin`: exact progress only. Pinning is CSS sticky (lvh), smoothing is the conductor.
    onUpdate: (self) => conductor.setExact(self.progress),
    onRefresh: (self) => conductor.setExact(self.progress),
  })

  conductor.setExact(trigger.progress)
  conductor.settle()

  return {
    refresh: () => ScrollTrigger.refresh(),
    destroy: () => trigger.kill(),
  }
}

/**
 * Tick the conductor from gsap.ticker, after any Lenis callback registered earlier (callbacks run in
 * add order). `render` runs right after the tick in the same frame. Returns a stop function.
 */
export function driveFromGsapTicker(conductor: Conductor, render?: StateListener): () => void {
  const callback = (_time: number, deltaMs: number): void => {
    const state = conductor.tick(deltaMs / 1000)
    render?.(state)
  }
  gsap.ticker.add(callback)
  return () => gsap.ticker.remove(callback)
}
