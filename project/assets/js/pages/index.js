import { accountRequest } from '../account-api.js'

export default {
  delimiters: ['[[', ']]'],
  data() {
    return {
      title: 'Django + VueJs = ❤',
      joke: '',
      isLoading: false,
      showUsers: false,
      showAccount: false,
      showAccountMenu: false,
      isSigningOut: false,
      logoutHold: null,
      logoutHoldFrame: null,
      logoutHoldProgress: 0,
      accountView: 'login',
      accountResetKey: '',
    }
  },
  methods: {
    startLogoutHold(event) {
      if (this.isSigningOut || !event.isPrimary || event.button !== 0) return
      this.cancelLogoutHold()
      const hold = { pointerId: event.pointerId, startedAt: performance.now(), cancelled: false, completed: false }
      this.logoutHold = hold
      this.showAccountMenu = false
      event.currentTarget.setPointerCapture(event.pointerId)
      const update = now => {
        this.logoutHoldProgress = Math.min(100, (now - hold.startedAt) / 10)
        if (this.logoutHoldProgress >= 100) {
          hold.completed = true
          this.logoutHoldFrame = null
          this.signOut()
        } else this.logoutHoldFrame = requestAnimationFrame(update)
      }
      this.logoutHoldFrame = requestAnimationFrame(update)
    },
    moveLogoutHold(event) {
      if (event.pointerId !== this.logoutHold?.pointerId) return
      const rect = event.currentTarget.getBoundingClientRect()
      if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) {
        this.cancelLogoutHold()
      }
    },
    endLogoutHold(event) {
      if (event.pointerId === this.logoutHold?.pointerId) {
        this.moveLogoutHold(event)
        this.clearLogoutHold()
      }
    },
    clearLogoutHold() {
      if (this.logoutHoldFrame !== null) cancelAnimationFrame(this.logoutHoldFrame)
      this.logoutHoldFrame = null
      this.logoutHoldProgress = 0
    },
    cancelLogoutHold() {
      if (this.logoutHold) this.logoutHold.cancelled = true
      this.clearLogoutHold()
    },
    clickLogout(event) {
      if (this.isSigningOut || (event.detail !== 0 && (this.logoutHold?.cancelled || this.logoutHold?.completed))) return
      this.showAccountMenu = true
    },
    async signOut() {
      if (this.isSigningOut) return
      this.cancelLogoutHold()
      this.isSigningOut = true
      this.showAccountMenu = false
      try {
        await accountRequest('auth/session', 'delete', {})
        this.store.user = null
        await this.accountAuthenticated()
        this.showAccount = false
      } catch (error) {
        this.store.displayError(error.message || 'Abmelden fehlgeschlagen. Bitte versuche es erneut.')
      } finally {
        this.isSigningOut = false
      }
    },
    openAccount(view = 'login') {
      if (view !== 'reset' && this.accountResetKey) {
        this.accountResetKey = ''
        window.history.replaceState({}, '', '/')
      }
      this.showAccountMenu = false
      this.accountView = view
      this.showAccount = true
    },
    requestAccountLogin(event) {
      event.preventDefault()
      this.openAccount('login')
    },
    async accountAuthenticated() {
      if (this.store.user) this.store.user = (await this.api.get('users/me/')).data
      if (this.accountResetKey) {
        this.accountResetKey = ''
        window.history.replaceState({}, '', '/')
      }
    },
    loadJoke() {
      this.isLoading = true
      axios
        .get('https://api.chucknorris.io/jokes/random')
        .then(response => {
          this.joke = response.data.value
          const now = this.moment(new Date())
          this.store.displayMessage(`${now}: Joke loaded!`, 'success')
          this.isLoading = false
        })
        .catch(error => {
          console.error('Error loading joke:', error)
          this.store.displayMessage(error, 'error')
          this.isLoading = false
        })
    },
  },
  mounted() {
    window.addEventListener('account-login', this.requestAccountLogin)
    window.addEventListener('blur', this.cancelLogoutHold)
    document.addEventListener('visibilitychange', this.cancelLogoutHold)
    const params = new URLSearchParams(window.location.search)
    if (['login', 'signup', 'reset'].includes(params.get('account'))) {
      this.accountResetKey = params.get('key') || ''
      this.openAccount(params.get('account'))
    }
    this.loadJoke()
    setTimeout(() => {
      if (!this.showAccount) document.getElementById('title')?.focus()
    }, 500)
  },
  beforeUnmount() {
    this.cancelLogoutHold()
    window.removeEventListener('account-login', this.requestAccountLogin)
    window.removeEventListener('blur', this.cancelLogoutHold)
    document.removeEventListener('visibilitychange', this.cancelLogoutHold)
  },
}
