const client = axios.create({
  baseURL: '/_allauth/browser/v1/',
  xsrfHeaderName: 'X-CSRFTOKEN',
  xsrfCookieName: 'csrftoken',
  headers: { 'X-Requested-With': 'XMLHttpRequest' },
  validateStatus: status => status < 500,
})

export async function accountRequest(url, method = 'get', data, headers) {
  const response = await client.request({ url, method, data, headers })
  const result = response.data
  if (response.status === 429) throw { status: 429 }
  if (!result || typeof result !== 'object' || !Number.isInteger(result.status)) {
    throw new Error(response.status === 403
      ? 'Die Sitzung ist abgelaufen. Bitte lade die Seite neu.'
      : 'Die Anfrage konnte nicht verarbeitet werden.')
  }
  if (![200, 201, 202, 401].includes(result.status)) throw result
  return result
}

function decode(value) {
  const base64 = value.replace(/-/g, '+').replace(/_/g, '/')
  return Uint8Array.from(atob(base64), character => character.charCodeAt(0))
}

// Convert only WebAuthn's binary fields for browsers without the JSON helpers.
function publicKeyOptions(options, creating) {
  const key = structuredClone(options.publicKey)
  key.challenge = decode(key.challenge)
  if (creating) key.user.id = decode(key.user.id)
  for (const name of ['allowCredentials', 'excludeCredentials']) {
    if (key[name]) key[name] = key[name].map(item => ({ ...item, id: decode(item.id) }))
  }
  return key
}

function encode(value) {
  return btoa(String.fromCharCode(...new Uint8Array(value)))
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '')
}

export async function passkeyCredential(options, creating, signal) {
  if (!window.PublicKeyCredential || !navigator.credentials) {
    throw new Error('Dieser Browser unterstützt hier keine Passkeys. Bitte verwende HTTPS oder localhost.')
  }
  const publicKey = publicKeyOptions(options, creating)
  const credential = await navigator.credentials[creating ? 'create' : 'get']({ publicKey, signal })
  if (credential.toJSON) return credential.toJSON()
  const response = {}
  for (const name of ['clientDataJSON', 'attestationObject', 'authenticatorData', 'signature', 'userHandle']) {
    if (credential.response[name]) response[name] = encode(credential.response[name])
  }
  if (credential.response.getTransports) response.transports = credential.response.getTransports()
  return {
    id: credential.id, rawId: encode(credential.rawId), type: credential.type,
    response, clientExtensionResults: credential.getClientExtensionResults(),
  }
}
