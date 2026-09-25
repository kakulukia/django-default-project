import { useAppStore } from './store.js'
import BaseApp from './BaseApp.js'
import UserChange from './components/UserChange.js'

const config = JSON.parse(document.getElementById('app-config').textContent)

const { createApp } = Vue
const { createVuetify } = Vuetify
const { createPinia } = Pinia

const appOptions = window.__VUE_APP_OPTIONS__ || {}

const vuetify = createVuetify({
  theme: {
    themes: {
      light: config.theme.light,
    },
  },
})

const api = axios.create({
  baseURL: config.apiBaseUrl,
  xsrfHeaderName: config.csrfHeaderName,
  xsrfCookieName: config.csrfCookieName,
})

const pinia = createPinia()
const store = useAppStore(pinia)
const app = createApp(appOptions)
app.use(pinia)
app.use(vuetify)
app.use(BaseApp, { api, store, config })
app.component('user-change', UserChange)
app.mount('#app')
