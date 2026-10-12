const { createApp, h, ref } = Vue
const { createVuetify } = Vuetify
const { VApp, VMain, VContainer, VCard, VBtn, VTextField, VCheckbox, VAlert, VIcon, VTooltip, VTabs, VTab } = Vuetify.components
const config = JSON.parse(document.getElementById('app-config').textContent)
const vuetify = createVuetify({ theme: { defaultTheme: 'light', themes: { light: config.theme.light } } })
const content = document.getElementById('account-content').innerHTML
const embedded = window.self !== window.top
const webauthnError = ref('')
document.addEventListener('allauth.error', event => {
  event.preventDefault()
  webauthnError.value = 'Der Passkey-Vorgang konnte nicht abgeschlossen werden. Bitte versuche es erneut.'
})

// Render server content as HTML, never as a Vue template containing user input.
createApp({
  render: () => h(VApp, {}, () => h(VMain, { class: embedded ? '' : 'd-flex align-center' }, () =>
    h(VContainer, { class: embedded ? 'pa-0' : 'py-8', style: { maxWidth: embedded ? '100%' : '472px' } }, () => [
      !embedded ? h('header', { class: 'd-flex align-center justify-space-between mb-4' }, [
        h('span', { class: 'text-subtitle-1 font-weight-medium' }, 'Django Demo'),
        h(VBtn, { href: '/', variant: 'text', size: 'small' }, () => 'Zur Demo'),
      ]) : null,
      h(VCard, { class: 'pa-6', rounded: 'lg', elevation: embedded ? 0 : 2 }, () => [
        webauthnError.value ? h(VAlert, { type: 'error', variant: 'tonal', role: 'alert', class: 'mb-4' }, () => webauthnError.value) : null,
        h('div', { class: 'account-content', innerHTML: content }),
      ]),
    ]))),
}).use(vuetify).mount('#account-app')

// Small component mounts retain native forms and allauth's WebAuthn scripts.
document.querySelectorAll('[data-account-field]').forEach(container => {
  const input = container.querySelector('input')
  if (!input || !['text', 'email', 'password', 'number', 'checkbox'].includes(input.type)) return
  const help = container.querySelector('[data-account-help]')
  const errors = [...container.querySelectorAll('.errorlist li')].map(error => error.textContent)
  const props = Object.fromEntries([...input.attributes].map(attribute => [attribute.name, attribute.value]))
  delete props.value
  delete props.class
  delete props['aria-describedby']
  props.label = container.querySelector('label')?.textContent
  props.modelValue = input.type === 'checkbox' ? input.checked : input.value
  props.errorMessages = errors
  props.hideDetails = 'auto'
  props.variant = 'outlined'
  if (input.type === 'checkbox') {
    props.value = input.value
    delete props.checked
  }
  const slots = help ? { details: () => h('div', {}, [
    errors.length ? h('div', { class: 'text-error' }, errors.join(' ')) : null,
    h('div', { id: help.id, innerHTML: help.innerHTML }),
  ]) } : {}
  createApp({ render: () => h(input.type === 'checkbox' ? VCheckbox : VTextField, props, slots) })
    .use(vuetify).mount(container)
})

document.querySelectorAll('[data-account-actions]').forEach(actions => {
  const priority = { cancel: 0, secondary: 1, primary: 2 }
  const buttons = [...actions.children].filter(child => child.hasAttribute('data-account-button'))
  buttons.sort((a, b) => priority[a.dataset.accountAction] - priority[b.dataset.accountAction])
    .forEach(button => actions.append(button))
})

document.querySelectorAll('[data-account-button]').forEach((container, index) => {
  const button = container.firstElementChild
  const props = Object.fromEntries([...button.attributes].map(attribute => [attribute.name, attribute.value]))
  const label = button.innerHTML
  props.color = container.dataset.accountColor
  props.variant = container.dataset.accountButton === 'primary' ? 'flat' : container.dataset.accountButton
  props.size = container.dataset.accountSize
  if (container.dataset.accountIcon) {
    if (props.size === 'small') props.icon = true
    else {
      props.width = 48
      props.minWidth = 48
      props.class = 'px-0'
    }
    props['aria-label'] = button.textContent.trim()
    createApp({ render: () => h(VTooltip, {
      id: `account-tooltip-${index}`, text: props['aria-label'],
      location: container.dataset.accountTooltipLocation || 'top',
    }, {
      activator: ({ props: tooltipProps }) => h(VBtn, { ...props, ...tooltipProps },
        () => h(VIcon, { icon: container.dataset.accountIcon })),
    }) }).use(vuetify).mount(container)
    return
  }
  createApp({ render: () => h(VBtn, props, () => h('span', { innerHTML: label })) }).use(vuetify).mount(container)
})

document.querySelectorAll('[data-account-email]').forEach(form => {
  form.addEventListener('submit', event => {
    if (event.submitter?.name === 'action_remove' && !window.confirm(form.dataset.confirmRemove)) {
      event.preventDefault()
    }
  })
})

document.querySelectorAll('[data-account-alert]').forEach(container => {
  const content = container.innerHTML
  const level = container.dataset.accountAlert
  const type = ['error', 'warning', 'success', 'info'].includes(level) ? level : 'info'
  createApp({ render: () => h(VAlert, { type, variant: 'tonal' }, () => h('div', { innerHTML: content })) })
    .use(vuetify).mount(container)
})

const credentialTabs = document.querySelector('[data-account-credential-tabs]')
if (credentialTabs) {
  const selected = ref(credentialTabs.dataset.selectedMethod)
  const panels = [...document.querySelectorAll('[data-account-credential-panel]')]
  const select = method => {
    selected.value = method
    panels.forEach(panel => { panel.hidden = panel.dataset.accountCredentialPanel !== method })
  }
  createApp({ render: () => h(VTabs, {
    modelValue: selected.value, 'onUpdate:modelValue': select, grow: true,
    color: 'primary', 'aria-label': 'Anmeldemethode',
  }, () => [
    h(VTab, { value: 'passkey', prependIcon: 'mdi-fingerprint', id: 'credential-passkey-tab',
      'aria-controls': 'credential-passkey' }, () => 'Passkey'),
    h(VTab, { value: 'password', prependIcon: 'mdi-form-textbox', id: 'credential-password-tab',
      'aria-controls': 'credential-password' }, () => 'Passwort'),
  ]) }).use(vuetify).mount(credentialTabs)
}

if (embedded) {
  document.body.classList.add('account-embedded')
  const card = document.querySelector('#account-app .v-card')
  new ResizeObserver(() => {
    window.parent.postMessage({ type: 'account-resize', height: card.getBoundingClientRect().height }, window.location.origin)
  }).observe(card)
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') window.parent.postMessage({ type: 'account-close' }, window.location.origin)
  })
}
