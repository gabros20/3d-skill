'use client'
/**
 * adapters/motion.ts: feeds the conductor from Motion's `useScroll` (React + Motion repos).
 *
 * Owns: one hook that forwards `scrollYProgress` into the conductor and rehydrates on mount.
 * Must not: bind the scroll value to a `style` prop (Motion can hand it to a native timeline that
 * drifts back past the input range), add a `useSpring` (the conductor smooths once), or measure a
 * sticky element (measure the range wrapper). Under Lenis, drive Lenis from Motion's frame loop
 * (`frame.setup`), see references/scroll-adapters.md.
 */
import { useEffect, type RefObject } from 'react'
import { useMotionValueEvent, useScroll, type UseScrollOptions } from 'motion/react'
import type { ConductorInput } from '../conductor'

// Module scope: a fresh offset array each render resubscribes.
const RANGE: NonNullable<UseScrollOptions['offset']> = ['start start', 'end end']

export function useMotionScrollConductor(
  conductor: ConductorInput,
  wrapper: RefObject<HTMLElement | null>,
): void {
  const { scrollYProgress } = useScroll({ target: wrapper, offset: RANGE })

  useMotionValueEvent(scrollYProgress, 'change', (progress) => {
    conductor.setExact(progress)
  })

  // 'change' does not fire on mount or after a restore: derive once, then snap smooth to it.
  useEffect(() => {
    conductor.setExact(scrollYProgress.get())
    conductor.settle()
  }, [conductor, scrollYProgress])
}
