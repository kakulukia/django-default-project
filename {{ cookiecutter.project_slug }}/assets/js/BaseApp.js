export default {
  install(app, { api, store, config }) {
    app.config.globalProperties.api = api
    app.config.globalProperties.store = store

    app.config.globalProperties.handleNotificationClick = notification => {
      if (!notification?.action) return

      if (notification.action === 'redirectToLogin') {
        window.location.href = '/admin/login/?next=' + window.location
      }
    }

    app.config.globalProperties.moment = value => moment(value).format('YYYY-MM-DD HH:mm')

    app.config.globalProperties.redirectToLogin = () => {
      window.location.href = '/admin/login/?next=' + window.location
    }

    app.config.globalProperties.waitUntilUserQueryDone = () => {
      return new Promise(resolve => {
        const interval = setInterval(() => {
          if (store.userQueryDone === true) {
            clearInterval(interval)
            resolve()
          }
        }, 100)
      })
    }

    if (config.stagingHost && window.location.hostname === config.stagingHost) {
      document.querySelector('.stage')?.classList.add('caution')
    }

    store.removeOldNotifications()

    api.interceptors.response.use(
      response => {
        const method = response.config.method?.toLowerCase()
        if ([200, 201].includes(response.status) && ['post', 'put', 'patch'].includes(method)) {
          store.displaySuccess('Saved!')
        }
        return response
      },
      error => {
        if (error.response?.data?.detail) {
          let message = error.response.data.detail
          let action = ''
          if (error.response.status === 403 && error.config?.url === 'users/me/') {
            message += ' (Click to Login)'
            action = 'redirectToLogin'
          }
          store.displayError(message, action)
          return Promise.reject(error)
        }

        if (!error.response) {
          store.displayError('Network error')
          return Promise.reject(error)
        }

        if (error.response.status === 401) {
          store.displayError('Unauthorized')
          return Promise.reject(error)
        }
        if (error.response.status === 403) {
          store.displayError('Forbidden')
          return Promise.reject(error)
        }
        if (error.response.status === 404) {
          store.displayError('Not Found')
          return Promise.reject(error)
        }

        store.displayError('Request failed')
        return Promise.reject(error)
      },
    )

    api
      .get('users/me/')
      .then(response => {
        store.user = response.data
        store.userQueryDone = true
      })
      .catch(error => {
        store.userQueryDone = true
        if (error.response?.status === 401) {
          // optional: redirect to a dedicated frontend login flow
        }
      })
  },
}
