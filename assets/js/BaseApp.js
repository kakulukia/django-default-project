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
        moment(value) {
          return moment(value).format('YYYY-MM-DD HH:mm')
        },
      },
      computed: {
      },
    });
  },
};
