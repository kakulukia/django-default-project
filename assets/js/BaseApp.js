export default {
  install(app) {
    app.mixin({
      delimiters: ['[[', ']]'],
      data() {
        return {
        };
      },
      methods: {
        handleNotificationClick(event) {
          const target = event.target;
          console.log('Notification clicked:', event, target.dataset.action);
          const action = target && target.dataset && target.dataset.action;
          if (action && typeof this[action] === 'function') {
            // Rufe die Methode aus der Vue-Instanz dynamisch auf
            this[action]();
          }
        },
        moment(value) {
          return moment(value).format('YYYY-MM-DD HH:mm')
        },
        redirectToLogin() {
          window.location.href = '/admin/login/?next=' + window.location
        },
      },
      computed: {
      },
      created() {
        // ensure the code is only run once
        if (this.$root !== this) return

        // start the notification removal process
        this.store.removeOldNotifications()

        api.interceptors.response.use(
          response => {
            if ([200, 201].includes(response.status) && ['post', 'put', 'patch'].includes(response.config.method.toLowerCase())) {
              this.store.displaySuccess("Gespeichert!");
            }
            return response;
          },
          error => {
            if (error.response && error.response.data && error.response.data.detail) {
              let message = error.response.data.detail
              let action = ''
              if (error.response.status === 403 && error.config.url === 'users/me/') {
                message += ' (Click to Login)'
                action = 'redirectToLogin'
              }
              this.store.displayError(message, action)
              return Promise.reject(error)
            }
            if (!error.response) {
              this.store.displayError('Network error')
              return Promise.reject(error)
            }
            if (error.response.status === 401) {
              this.store.displayError('Unauthorized')
              return Promise.reject(error)
            }
            if (error.response.status === 403) {
              this.store.displayError('Forbidden')
              return Promise.reject(error)
            }
            if (error.response.status === 404) {
              this.store.displayError('Not Found')
              return Promise.reject(error)
            }
          }
        )

        // check if we are actually logged in
        api.get('users/me/')
          .then(response => {
            this.store.user = response.data

          }).catch(error => {
            if (error.response.status === 401) {
              // TODO: change the login url to a frontend location if there is one
              // this.redirectToLogin()
            }

          })
      }
    })
  },
}
