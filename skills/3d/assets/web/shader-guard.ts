/**
 * shader-guard.ts: make a failed shader program loud on `WebGLRenderer`. Copy and own.
 *
 * Owns: `renderer.debug.onShaderError` (which REPLACES three's own console error, so this logs),
 * keeping `debug.checkShaderErrors` on, and the verdict after a warm render. Must not: render,
 * reveal or decide the fallback; the caller does (r3f/SceneCanvas.tsx sets data-scene-mode="error").
 *
 * three r186 source (WebGLProgram.js `onFirstUse`): link status, `onShaderError` and
 * `program.diagnostics` exist only while `checkShaderErrors` is true, and only after the program's
 * FIRST USE in a draw. `compileAsync` alone never fills them: check after one real render through
 * the full chain. `diagnostics` is set for every failed program and for successful ones only when
 * a driver log exists, so "no diagnostics" means fine.
 */
import type { WebGLRenderer } from 'three'

export type ShaderVerdict = { ok: true } | { ok: false; reason: string }

interface ProgramDiagnostics {
  runnable: boolean
  programLog?: string
  vertexShader?: { log?: string }
  fragmentShader?: { log?: string }
}

/** Pure: the verdict from the errors the handler saw and `renderer.info.programs` after a warm render. */
export function shaderVerdict(errors: readonly string[], programs: readonly unknown[] | null | undefined): ShaderVerdict {
  if (errors.length) return { ok: false, reason: errors[0] as string }
  for (const p of programs ?? []) {
    const d = (p as { diagnostics?: ProgramDiagnostics } | null)?.diagnostics
    if (d && d.runnable === false) {
      const name = (p as { name?: string }).name || 'program'
      const log = d.programLog || d.fragmentShader?.log || d.vertexShader?.log || 'not runnable'
      return { ok: false, reason: `${name}: ${log}` }
    }
  }
  return { ok: true }
}

export interface ShaderGuard {
  /** Call after the warm render: the handler's errors plus every program's diagnostics. */
  check(): ShaderVerdict
  /** Restores the previous handler. */
  dispose(): void
}

/**
 * Install before the first render. `onError` fires at a failure's first use, at any time (a late
 * material swap too), so the caller can drop to the fallback even after the reveal.
 */
export function guardShaders(renderer: WebGLRenderer, onError?: (reason: string) => void): ShaderGuard {
  const errors: string[] = []
  const previous = renderer.debug.onShaderError
  // Off silences both mechanisms; production speed is not worth a scene that fails silently.
  renderer.debug.checkShaderErrors = true
  renderer.debug.onShaderError = (gl, program, vs, fs) => {
    const raw = program as unknown as globalThis.WebGLProgram // three passes the GL program, not its wrapper
    const log = gl.getProgramInfoLog(raw) || gl.getShaderInfoLog(fs) || gl.getShaderInfoLog(vs) || 'link failed'
    const reason = log.trim()
    errors.push(reason)
    console.error('[scene] shader program failed:', reason)
    onError?.(reason)
  }
  return {
    check: () => shaderVerdict(errors, renderer.info.programs),
    dispose: () => {
      renderer.debug.onShaderError = previous
    },
  }
}
