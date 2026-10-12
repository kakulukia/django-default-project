const UserChange = {
  delimiters: ['[[', ']]'],
  template: '#user-change-template',
  data() {
    return {
      users: [],
      username: '',
    }
  },
  watch: {
    'store.user.id'() {
      if (this.store.user) this.loadUsers()
      else this.users = []
    },
  },
  methods: {
    updateUser(user) {
      this.api.patch(`users/${user.id}/`, { username: user.username }).then(() => {
        this.store.displayMessage(
          "You can't imagine the joy of " + user.username + ' once he/she finds out!',
          'warning',
        )
      })
    },
    addUser() {
      this.api.post('users/', { username: this.username }).then(() => {
        this.username = ''
        this.loadUsers()
      })
    },
    loadUsers() {
      this.api.get('users/').then(response => {
        this.users = response.data
      })
    },
  },
  mounted() {
    this.waitUntilUserQueryDone().then(() => {
      if (this.store.user) this.loadUsers()
    })
  },
}

export default UserChange
