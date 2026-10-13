import { accountRequest, passkeyCredential } from '../account-api.js'

export default {
  template: '#account-dialog-template',
  delimiters: ['[[', ']]'],
  props: { modelValue: Boolean, initialView: { type: String, default: 'login' }, resetKey: String },
  emits: ['update:modelValue', 'authenticated'],
  data() {
    return {
      view: 'login', ready: false, busy: false,
      login: '', email: new URLSearchParams(window.location.search).get('email') || '',
      password: '', password2: '', code: '',
      credentialTab: 'passkey', name: 'Hauptschlüssel',
      emails: [], authenticators: [], recoveryCodes: [],
      totpActive: false, totpSetup: null,
      confirmAction: null, resumeView: 'passkeys', mfaTypes: [], mfaMethod: 'passkey',
      passkeyAbort: null,
    }
  },
  computed: {
    title() {
      return {
        login: 'Anmeldung', signup: 'Registrieren', verify: 'E-Mail bestätigen',
        credentials: 'Anmeldung einrichten', reset: 'Passwort zurücksetzen',
        resetPassword: 'Neues Passwort',
        emails: 'E-Mail-Adressen', passkeys: 'Passkeys',
        totp: 'Zwei-Faktor-Authentifizierung',
        reauthenticate: 'Anmeldung bestätigen', mfa: 'Anmeldung bestätigen',
      }[this.view] || 'Konto'
    },
  },
  watch: {
    modelValue(open) {
      if (open) this.run(this.prepare)
      else {
        this.passkeyAbort?.abort()
        this.password = this.password2 = ''
      }
    },
    initialView() {
      if (this.modelValue) this.run(this.prepare)
    },
  },
  methods: {
    close() { this.$emit('update:modelValue', false) },
    afterLeave() {
      if (!this.modelValue) {
        this.ready = false
        this.totpSetup = null
      }
      this.recoveryCodes = []
    },
    go(view) {
      this.view = view
      this.password = this.password2 = this.code = ''
      this.confirmAction = null
      if (view === 'emails') this.email = ''
      if (view === 'credentials') this.credentialTab = 'passkey'
    },
    async run(action) {
      if (this.busy) return
      this.busy = true
      try { await action.call(this) }
      catch (error) {
        if (error.handled || error.name === 'AbortError') return
        if (error.name === 'NotAllowedError') {
          this.store.displayMessage('Die Passkey-Anfrage wurde abgebrochen oder nicht bestätigt. Du kannst es erneut versuchen.', 'warning')
        } else {
          const messages = error.errors?.length ? error.errors.map(item => item.message) : [
            error.status === 429 ? 'Zu viele Versuche. Bitte warte kurz und versuche es erneut.'
              : error.status === 409 ? 'Dieser Schritt ist abgelaufen. Bitte beginne die Anmeldung erneut.'
                : error.message || 'Die Anfrage ist fehlgeschlagen. Bitte versuche es erneut.',
          ]
          this.store.displayError(messages.join(' '))
        }
      } finally {
        this.passkeyAbort = null
        this.busy = false
      }
    },
    async request(url, method, data, headers) {
      const result = await accountRequest(url, method, data, headers)
      if (result.status === 401 && url.startsWith('account/')) {
        this.resumeView = this.view
        await this.acceptAuth(result, false)
        if (!result.meta?.is_authenticated) this.go('login')
        throw { handled: true }
      }
      return result
    },
    async open() {
      this.go(this.initialView)
      this.recoveryCodes = []
      this.totpSetup = null
      const result = await this.request('auth/session')
      const pending = await this.acceptAuth(result, false)
      if (pending) return
      if (this.resetKey) {
        await this.request('auth/password/reset', 'get', undefined, { 'X-Password-Reset-Key': this.resetKey })
        this.go('resetPassword')
      } else if (this.store.user) {
        if (this.view === 'login' || this.view === 'signup') this.go('passkeys')
        await this.loadManagement()
      } else if (['emails', 'passkeys', 'totp'].includes(this.view)) this.go('login')
    },
    async prepare() {
      this.ready = false
      try { await this.open() }
      finally { this.ready = this.modelValue }
    },
    async acceptAuth(result, finish = true) {
      if (result.meta?.is_authenticated) {
        this.store.user = result.data.user
        if (result.status === 401) {
          this.go('reauthenticate')
          return true
        }
        if (finish) {
          this.password = this.password2 = ''
          this.$emit('authenticated')
          this.close()
        }
        return false
      }
      this.store.user = null
      const pending = result.data?.flows?.find(flow => flow.is_pending)
      if (pending) {
        const views = { verify_email: 'verify', mfa_signup_webauthn: 'credentials', mfa_authenticate: 'mfa' }
        this.go(views[pending.id] || 'login')
        this.mfaTypes = pending.types || []
        this.selectMfaMethod(this.mfaTypes.includes('webauthn') ? 'passkey'
          : this.mfaTypes.includes('totp') ? 'totp' : 'recovery_codes')
        return true
      }
      if (finish) this.go('login')
      return false
    },
    async signIn() {
      const identifier = this.login.trim()
      const result = await this.request('auth/login', 'post', {
        [identifier.includes('@') ? 'email' : 'username']: identifier, password: this.password,
      })
      await this.acceptAuth(result)
    },
    async signUp() {
      await this.acceptAuth(await this.request('auth/signup', 'post', { email: this.email }))
    },
    async verifyEmail() {
      const result = await this.request('auth/email/verify', 'post', { key: this.code })
      if (this.store.user && result.status === 200) {
        this.go('emails')
        await this.loadManagement()
        this.store.displaySuccess('E-Mail-Adresse bestätigt.')
      } else await this.acceptAuth(result)
    },
    async resendCode() {
      await this.request('auth/email/verify/resend', 'post', {})
      this.store.displaySuccess('Ein neuer Code wurde versendet.')
    },
    checkPasswords() {
      if (!this.password || this.password !== this.password2) {
        throw new Error('Bitte gib das Passwort zweimal übereinstimmend ein.')
      }
    },
    async setSignupPassword() {
      this.checkPasswords()
      await this.acceptAuth(await this.request('auth/signup/password', 'post', {
        password1: this.password, password2: this.password2,
      }))
    },
    async resetPasswordRequest() {
      await this.request('auth/password/request', 'post', { email: this.email })
      this.go('login')
      this.store.displaySuccess('Wir haben dir eine E-Mail mit den nächsten Schritten gesendet. Bitte prüfe auch deinen Spamordner.')
    },
    async saveResetPassword() {
      this.checkPasswords()
      const result = await this.request('auth/password/reset', 'post', { key: this.resetKey, password: this.password })
      if (result.status === 401 && result.data?.flows?.some(flow => flow.is_pending)) {
        await this.acceptAuth(result)
      } else {
        this.store.user = result.meta?.is_authenticated ? result.data.user : null
        this.go('login')
        this.store.displaySuccess('Dein Passwort wurde gespeichert. Du kannst dich jetzt anmelden.')
        this.$emit('authenticated')
      }
    },
    async usePasskey(mode) {
      const creating = ['signup', 'add'].includes(mode)
      const url = {
        signup: 'auth/webauthn/signup', add: 'account/authenticators/webauthn?passwordless',
        login: 'auth/webauthn/login', mfa: 'auth/webauthn/authenticate',
        reauthenticate: 'auth/webauthn/reauthenticate',
      }[mode]
      const result = await this.request(url)
      this.passkeyAbort = new AbortController()
      const credential = await passkeyCredential(
        result.data[creating ? 'creation_options' : 'request_options'], creating, this.passkeyAbort.signal,
      )
      const saved = await this.request(url, mode === 'signup' ? 'put' : 'post', {
        credential, name: this.name, ...(mode === 'add' ? { passwordless: true } : {}),
      })
      this.passkeyAbort = null
      if (mode === 'add') {
        await this.loadManagement()
        this.store.displaySuccess('Passkey gespeichert.')
      } else if (mode === 'reauthenticate') await this.finishReauthentication(saved)
      else await this.acceptAuth(saved)
    },
    async reauthenticate() {
      await this.finishReauthentication(await this.request('auth/reauthenticate', 'post', { password: this.password }))
    },
    async finishReauthentication(result) {
      if (result.status !== 200) return this.acceptAuth(result, false)
      this.go(this.resumeView)
      await this.loadManagement()
      this.store.displaySuccess('Anmeldung bestätigt. Bitte führe die gewünschte Aktion erneut aus.')
    },
    async authenticateCode() {
      await this.acceptAuth(await this.request('auth/2fa/authenticate', 'post', { code: this.code }))
    },
    selectMfaMethod(method) {
      this.mfaMethod = method
      this.code = ''
    },
    async loadManagement() {
      if (this.view === 'emails') this.emails = (await this.request('account/email')).data
      if (this.view === 'passkeys') {
        this.authenticators = (await this.request('account/authenticators')).data.filter(item => item.type === 'webauthn')
      }
      if (this.view === 'totp') await this.loadTotp()
    },
    async loadTotp() {
      this.totpSetup = null
      try {
        await this.request('account/authenticators/totp')
        this.totpActive = true
      } catch (error) {
        if (error.status !== 404 || !error.meta?.secret) throw error
        this.totpActive = false
        this.totpSetup = error.meta
      }
    },
    async activateTotp() {
      await this.request('account/authenticators/totp', 'post', { code: this.code })
      this.totpActive = true
      this.totpSetup = null
      this.code = ''
      this.store.displaySuccess('Zwei-Faktor-Authentifizierung aktiviert. Bewahre deine Wiederherstellungscodes sicher auf.')
    },
    async deactivateTotp() {
      await this.request('account/authenticators/totp', 'delete', {})
      this.confirmAction = null
      this.recoveryCodes = []
      await this.loadTotp()
      this.store.displaySuccess('Zwei-Faktor-Authentifizierung deaktiviert.')
    },
    async emailAction(method, address) {
      await this.request('account/email', method, { email: address, ...(method === 'patch' ? { primary: true } : {}) })
      this.confirmAction = null
      if (method === 'post' || method === 'put') {
        this.go('verify')
        this.store.displayMessage('Bitte bestätige die E-Mail-Adresse mit dem zugesendeten Code.')
      } else {
        await this.loadManagement()
        this.store.displaySuccess(method === 'patch' ? 'Primäre E-Mail-Adresse festgelegt.' : 'E-Mail-Adresse entfernt.')
      }
    },
    async removePasskey(id) {
      await this.request('account/authenticators/webauthn', 'delete', { authenticators: [id] })
      this.confirmAction = null
      await this.loadManagement()
    },
    async renamePasskey(authenticator) {
      await this.request('account/authenticators/webauthn', 'put', { id: authenticator.id, name: authenticator.name })
      this.store.displaySuccess('Name gespeichert.')
    },
    async showRecoveryCodes(generate = false) {
      let result
      try {
        result = await this.request('account/authenticators/recovery-codes', generate ? 'post' : 'get', {})
      } catch (error) {
        if (error.status !== 404) throw error
        this.store.displayMessage('Noch keine Wiederherstellungscodes vorhanden. Erstelle zuerst einen Passkey.')
        return
      }
      this.recoveryCodes = result.data.unused_codes || []
      this.confirmAction = null
      if (!this.recoveryCodes.length) this.store.displayMessage('Diese Codes sind nicht mehr verfügbar. Erzeuge bei Bedarf neue Codes.')
    },
    async cancel() {
      if (['verify', 'credentials', 'mfa'].includes(this.view) && !this.store.user) {
        await this.request('auth/session', 'delete', {})
      }
      this.close()
    },
  },
}
