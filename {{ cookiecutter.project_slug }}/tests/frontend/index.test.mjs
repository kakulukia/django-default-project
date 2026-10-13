import assert from 'node:assert/strict'
import test from 'node:test'

const client = {}
globalThis.axios = { create: () => client }
const { default: page } = await import('../../assets/js/pages/index.js')
let nextFrame = 0
const frames = new Map()
globalThis.requestAnimationFrame = callback => {
  frames.set(++nextFrame, callback)
  return nextFrame
}
globalThis.cancelAnimationFrame = id => frames.delete(id)

function advanceFrame(now) {
  const pending = [...frames.values()]
  frames.clear()
  pending.forEach(callback => callback(now))
}

function pointer(overrides = {}) {
  return {
    pointerId: 1, isPrimary: true, button: 0, clientX: 20, clientY: 20,
    currentTarget: {
      setPointerCapture() {},
      getBoundingClientRect: () => ({ left: 0, right: 48, top: 0, bottom: 48 }),
    },
    ...overrides,
  }
}

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

test('Short mouse and touch presses open the menu without signing out', t => {
  t.mock.method(performance, 'now', () => 0)
  for (const pointerType of ['mouse', 'touch']) {
    const { state } = pageState()
    state.signOut = () => assert.fail('A short press must not sign out')
    state.startLogoutHold(pointer({ pointerType }))
    advanceFrame(500)
    assert.equal(state.logoutHoldProgress, 50)
    state.endLogoutHold(pointer())
    state.clickLogout({ detail: 1 })
    advanceFrame(1200)
    assert.equal(state.showAccountMenu, true)
    assert.equal(state.logoutHoldProgress, 0)
    assert.equal(frames.size, 0)
  }
})

test('A full one-second hold signs out exactly once and does not reopen the menu', async t => {
  t.mock.method(performance, 'now', () => 0)
  const { state } = pageState()
  let calls = 0
  let pending
  const signOut = state.signOut
  state.signOut = () => { pending = signOut() }
  client.request = async () => {
    calls++
    return { status: 401, data: { status: 401, meta: { is_authenticated: false } } }
  }
  state.startLogoutHold(pointer())
  advanceFrame(999)
  assert.equal(calls, 0)
  advanceFrame(1000)
  await pending
  state.endLogoutHold(pointer())
  state.clickLogout({ detail: 1 })
  advanceFrame(2000)
  assert.equal(calls, 1)
  assert.equal(state.store.user, null)
  assert.equal(state.showAccountMenu, false)
  assert.equal(frames.size, 0)
})

test('Dragging away or cancelling prevents both logout and the trailing click', t => {
  t.mock.method(performance, 'now', () => 0)
  for (const cancel of [
    state => state.moveLogoutHold(pointer({ clientX: 70 })),
    state => state.endLogoutHold(pointer({ clientY: 70 })),
    state => state.cancelLogoutHold(),
  ]) {
    const { state } = pageState()
    state.signOut = () => assert.fail('A cancelled hold must not sign out')
    state.startLogoutHold(pointer())
    advanceFrame(400)
    cancel(state)
    state.endLogoutHold(pointer())
    state.clickLogout({ detail: 1 })
    advanceFrame(1200)
    assert.equal(state.showAccountMenu, false)
    assert.equal(state.logoutHoldProgress, 0)
    assert.equal(frames.size, 0)
    state.clickLogout({ detail: 0 })
    assert.equal(state.showAccountMenu, true)
  }
})

test('Secondary buttons, secondary pointers and pending logout cannot start a hold', () => {
  const { state } = pageState()
  for (const event of [pointer({ button: 2 }), pointer({ isPrimary: false })]) state.startLogoutHold(event)
  state.isSigningOut = true
  state.startLogoutHold(pointer())
  state.clickLogout({ detail: 0 })
  assert.equal(frames.size, 0)
  assert.equal(state.showAccountMenu, false)
})

test('Unmount cancels an active hold so it cannot log out later', t => {
  t.mock.method(performance, 'now', () => 0)
  const { state } = pageState()
  state.signOut = () => assert.fail('An unmounted page must not sign out')
  const previousWindow = globalThis.window
  const previousDocument = globalThis.document
  globalThis.window = globalThis.document = { removeEventListener() {} }
  t.after(() => {
    globalThis.window = previousWindow
    globalThis.document = previousDocument
  })
  state.startLogoutHold(pointer())
  page.beforeUnmount.call(state)
  advanceFrame(1500)
  assert.equal(frames.size, 0)
  assert.equal(state.logoutHoldProgress, 0)
})
