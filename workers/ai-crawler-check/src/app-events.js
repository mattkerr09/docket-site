// Shared by the public route and the tally store. No request details belong in a tally.
export const APP_EVENTS = ['first_opened', 'first_audit_finished', 'free_limit']
export const APP_SYSTEMS = ['mac', 'windows', 'linux']
const VERSION = /^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$/
const validVersion = (v) => VERSION.test(v) && v === v.trim()

export function appTallyKeys(params) {
  // Ambiguous repeated fields are invalid. All other query parameters are ignored.
  if (['e', 'v', 'os'].some((key) => params.getAll(key).length !== 1)) return []
  const event = params.get('e'), version = params.get('v'), system = params.get('os')
  if (!APP_EVENTS.includes(event) || !validVersion(version) || !APP_SYSTEMS.includes(system)) return []
  return [`app:${event}`, `app:${event}:${version}`, `app:${event}:${system}`]
}

export function validAppTallyKey(key) {
  const [prefix, event, dimension, ...extra] = key.split(':')
  return prefix === 'app' && APP_EVENTS.includes(event) && extra.length === 0
    && (dimension === undefined || APP_SYSTEMS.includes(dimension) || validVersion(dimension))
}
