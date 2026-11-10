export const realClock = {
  now: () => Date.now(),
  sleep: (ms) => new Promise((resolve) => setTimeout(resolve, ms)),
  setTimeout: (fn, ms) => setTimeout(fn, ms),
  clearTimeout: (id) => clearTimeout(id),
}

export class Stopped extends Error {}

// Reject even if a fake, stalled stream or upstream fetch ignores abort. The
// operation also gets the signal so it cannot start a later redirect or read.
export async function bounded(clock, until, action, parent) {
  if (clock.now() >= until || parent?.aborted) throw new Stopped('The check ran out of time.')
  const controller = new AbortController()
  let timer
  let abort
  const stopped = new Promise((_, reject) => {
    abort = () => { controller.abort(); reject(new Stopped('The check ran out of time.')) }
    parent?.addEventListener('abort', abort, { once: true })
    timer = clock.setTimeout(abort, until - clock.now())
  })
  try {
    return await Promise.race([action(controller.signal), stopped])
  } finally {
    clock.clearTimeout(timer)
    parent?.removeEventListener('abort', abort)
    controller.abort()
  }
}

export async function readCapped(response, max, signal) {
  if (!response.body) return { text: '', bytes: 0, truncated: false }
  const reader = response.body.getReader()
  const buffer = new Uint8Array(max)
  let bytes = 0
  let truncated = false
  const cancel = () => { Promise.resolve(reader.cancel()).catch(() => {}) }
  signal?.addEventListener('abort', cancel, { once: true })
  try {
    for (;;) {
      signal?.throwIfAborted()
      const { done, value } = await reader.read()
      signal?.throwIfAborted()
      if (done) break
      const room = max - bytes
      const part = value.subarray(0, room)
      buffer.set(part, bytes)
      bytes += part.byteLength
      if (bytes >= max) { truncated = true; cancel(); break }
    }
  } catch (error) {
    cancel()
    throw error
  } finally {
    signal?.removeEventListener('abort', cancel)
  }
  return { text: new TextDecoder().decode(buffer.subarray(0, bytes)), bytes, truncated }
}

export function discard(response) {
  if (response.body) Promise.resolve(response.body.cancel()).catch(() => {})
}
