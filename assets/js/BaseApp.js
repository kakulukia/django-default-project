export default {
  install(app) {
    app.mixin({
      delimiters: ['[[', ']]'],
      data() {
        return {
          message: '',
          snackbar: false,
          snackbarColor: '',
          user: undefined,
        };
      },
      methods: {
        displayMessage(message, color = '') {
          this.message = message
          this.snackbarColor = color
          this.snackbar = true
        },
        displayError(message) {
          this.displayMessage(message, 'error')
        },
        displaySuccess(message) {
          this.displayMessage(message, 'success')
        },
        moment(value) {
          return moment(value).format('YYYY-MM-DD HH:mm')
        },
      },
      computed: {
      },
      created() {
        // ensure the code is only run once
        if (this.$root !== this) return

        api.interceptors.response.use(
          response => response,
          error => {
            if (error.response && error.response.data && error.response.data.detail) {
              this.displayError(error.response.data.detail)
              return Promise.reject(error)
            }
            if (!error.response) {
              this.displayError('Network error')
              return Promise.reject(error)
            }
            if (error.response.status === 401) {
              this.displayError('Unauthorized')
              return Promise.reject(error)
            }
            if (error.response.status === 403) {
              this.displayError('Forbidden')
              return Promise.reject(error)
            }
            if (error.response.status === 404) {
              this.displayError('Not Found')
              return Promise.reject(error)
            }
          }
        )

        // check if we are actually logged in
        api.get('users/me/')
          .then(response => {
            this.user = response.data

          }).catch(error => {
            if (error.response.status === 403) {
              // TODO: change the lofin url to a frontend location if there is one
              window.location.href = '/admin/login/?next=' + window.location
            }
          })
      }
    })
  },
}
