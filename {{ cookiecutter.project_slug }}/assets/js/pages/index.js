export default {
  delimiters: ['[[', ']]'],
  data() {
    return {
      title: 'Django + VueJs = ❤',
      joke: '',
      isLoading: false,
    }
  },
  methods: {
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
    this.loadJoke()
    setTimeout(() => {
      title.focus()
    }, 500)
  },
}
