import assert from 'node:assert/strict'
import test from 'node:test'

globalThis.axios = { create: () => ({}) }
globalThis.window = { location: { search: '' } }
const { default: dialog } = await import('../../assets/js/components/AccountDialog.js')

async function pendingMfa(types) {
  const state = dialogState()
  await state.acceptAuth({ status: 401, data: { flows: [{ id: 'mfa_authenticate', is_pending: true, types }] } })
  assert.equal(state.view, 'mfa')
  return state
}

function dialogState() {
  const notifications = []
  const state = {
    ...dialog.data(), notifications,
    store: {
      user: null,
      displayMessage: (message, type = 'info') => notifications.push({ message, type }),
      displayError: message => notifications.push({ message, type: 'error' }),
      displaySuccess: message => notifications.push({ message, type: 'success' }),
    },
  }
  for (const [name, method] of Object.entries(dialog.methods)) state[name] = method.bind(state)
  return state
}

test('TOTP setup is not active until a valid code is accepted', async () => {
  const state = dialogState()
  const setup = { secret: 'LOCAL-TEST-SECRET', qr_svg: '<svg />' }
  state.request = async () => { throw { status: 404, meta: setup } }
  await state.loadTotp()
  assert.equal(state.totpActive, false)
  assert.equal(state.totpSetup, setup)
  state.code = 'invalid'
  state.request = async () => { throw { status: 400, errors: [{ message: 'Ungültiger Code.' }] } }
  await state.run(state.activateTotp)
  assert.equal(state.totpActive, false)
  assert.equal(state.totpSetup, setup)
  assert.equal(state.notifications[0].type, 'error')
  state.code = '123456'
  state.request = async (url, method, data) => {
    assert.equal(url, 'account/authenticators/totp')
    assert.equal(method, 'post')
    assert.deepEqual(data, { code: '123456' })
    return { status: 200 }
  }
  await state.run(state.activateTotp)
  assert.equal(state.totpActive, true)
  assert.equal(state.totpSetup, null)
  assert.equal(state.code, '')
  assert.equal(state.notifications[1].type, 'success')
})

test('Leaving TOTP setup clears the sensitive setup data', () => {
  const state = dialogState()
  state.modelValue = false
  state.totpSetup = { secret: 'LOCAL-TEST-SECRET' }
  state.afterLeave()
  assert.equal(state.totpSetup, null)
})

for (const [types, expected] of [
  [['webauthn'], 'passkey'],
  [['webauthn', 'recovery_codes'], 'passkey'],
  [['totp', 'recovery_codes'], 'totp'],
  [['webauthn', 'totp', 'recovery_codes'], 'passkey'],
]) {
  test(`Pending MFA with ${types.join(', ')} starts with ${expected}`, async () => {
    const state = await pendingMfa(types)
    assert.equal(state.mfaMethod, expected)
    assert.equal(state.code, '')
  })
}

test('Recovery codes require explicit selection and switching clears stale input', async () => {
  const state = await pendingMfa(['webauthn', 'recovery_codes'])
  state.selectMfaMethod('recovery_codes')
  assert.equal(state.mfaMethod, 'recovery_codes')
  state.code = 'invalid-code'
  state.selectMfaMethod('passkey')
  assert.equal(state.mfaMethod, 'passkey')
  assert.equal(state.code, '')
})

for (const [error, type, message] of [
  [{ name: 'NotAllowedError' }, 'warning', 'Die Passkey-Anfrage wurde abgebrochen oder nicht bestätigt. Du kannst es erneut versuchen.'],
  [{ status: 429 }, 'error', 'Zu viele Versuche. Bitte warte kurz und versuche es erneut.'],
  [{ status: 409 }, 'error', 'Dieser Schritt ist abgelaufen. Bitte beginne die Anmeldung erneut.'],
  [new Error('Network error'), 'error', 'Network error'],
  [{ errors: [{ message: 'Invalid email' }, { message: 'Required field' }] }, 'error', 'Invalid email Required field'],
]) {
  test(`Account failure ${error.name || error.status || 'validation'} uses shared notifications`, async () => {
    const state = dialogState()
    await state.run(() => { throw error })
    assert.deepEqual(state.notifications, [{ message, type }])
    assert.equal(state.busy, false)
  })
}

test('Closing a passkey request and handled authentication changes stay silent', async () => {
  const state = dialogState()
  for (const error of [{ name: 'AbortError' }, { handled: true }]) {
    await state.run(() => { throw error })
  }
  assert.deepEqual(state.notifications, [])
  assert.equal(state.busy, false)
})

test('Resending verification code reports success through shared notifications', async () => {
  const state = dialogState()
  state.request = async () => ({ status: 200 })
  await state.run(state.resendCode)
  assert.deepEqual(state.notifications, [{ message: 'Ein neuer Code wurde versendet.', type: 'success' }])
})

test('Missing recovery codes report information through shared notifications', async () => {
  const state = dialogState()
  state.request = async () => { throw { status: 404 } }
  await state.run(state.showRecoveryCodes)
  assert.deepEqual(state.notifications, [{
    message: 'Noch keine Wiederherstellungscodes vorhanden. Erstelle zuerst einen Passkey.', type: 'info',
  }])
})

test('Requesting a password reset returns to login and notifies without a message-only dialog', async () => {
  const state = dialogState()
  state.view = 'reset'
  state.request = async () => ({ status: 200 })
  await state.run(state.resetPasswordRequest)
  assert.equal(state.view, 'login')
  assert.equal(state.notifications[0].type, 'success')
  assert.match(state.notifications[0].message, /E-Mail.*Spamordner/)
})
