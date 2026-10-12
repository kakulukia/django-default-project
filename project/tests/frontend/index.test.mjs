import assert from 'node:assert/strict'
import test from 'node:test'

const client = {}
globalThis.axios = { create: () => client }
const { default: page } = await import('../../assets/js/pages/index.js')

function pageState() {
  const errors = []
  const state = {
    ...page.data(),
    store: { user: { id: 1 }, displayError: message => errors.push(message) },
  }
  for (const [name, method] of Object.entries(page.methods)) state[name] = method.bind(state)
  return { state, errors }
}

test('Logout ends the session directly and closes the account UI', async () => {
  const { state, errors } = pageState()
  state.showAccount = state.showAccountMenu = true
  let calls = 0
  client.request = async request => {
    calls++
    assert.equal(request.url, 'auth/session')
    assert.equal(request.method, 'delete')
    assert.equal(state.isSigningOut, true)
    return { status: 401, data: { status: 401, meta: { is_authenticated: false } } }
  }
  await state.signOut()
  assert.equal(calls, 1)
  assert.equal(state.store.user, null)
  assert.equal(state.showAccountMenu, false)
  assert.equal(state.showAccount, false)
  assert.equal(state.isSigningOut, false)
  assert.deepEqual(errors, [])
})

test('Failed logout preserves the user and displays an error', async () => {
  const { state, errors } = pageState()
  client.request = async () => { throw new Error('Network error') }
  await state.signOut()
  assert.deepEqual(state.store.user, { id: 1 })
  assert.deepEqual(errors, ['Network error'])
  assert.equal(state.isSigningOut, false)
})

test('Repeated logout clicks share the pending operation', async () => {
  const { state } = pageState()
  let finish
  let calls = 0
  client.request = () => {
    calls++
    return new Promise(resolve => { finish = resolve })
  }
  const pending = state.signOut()
  await state.signOut()
  assert.equal(calls, 1)
  finish({ status: 401, data: { status: 401, meta: { is_authenticated: false } } })
  await pending
  assert.equal(state.store.user, null)
})
