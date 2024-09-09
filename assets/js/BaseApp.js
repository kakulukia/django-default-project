export default {
  install(app) {
    app.mixin({
      delimiters: ['[[', ']]'],
      data() {
        return {
          message: '',
          snackbar: false,
          snackbarColor: '',
        };
      },
      methods: {
        displayMessage(message, color = '') {
          this.message = message
          this.snackbarColor = color
          this.snackbar = true
        },
        getCSRFToken() {
          // https://docs.djangoproject.com/en/3.1/ref/csrf/#ajax
          // use it in axios like this:
          // axios.defaults.headers.common['X-CSRFToken'] = this.getCSRFToken();
          const value = `; ${document.cookie}`
          const parts = value.split('; csrftoken=')
          if (parts.length === 2) {
            const csrfToken = parts.pop().split(';').shift()
            return csrfToken
          }
          return {}
        },
        moment(value) {
          return moment(value).format('YYYY-MM-DD HH:mm')
        },
      },
      computed: {
      },
    });
  },
};
