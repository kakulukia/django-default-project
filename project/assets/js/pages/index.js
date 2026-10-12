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
      accountView: 'login',
      accountResetKey: '',
    }
  },
  methods: {
    async signOut() {
      if (this.isSigningOut) return
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
    window.removeEventListener('account-login', this.requestAccountLogin)
  },
}
