const UserChange = {
  delimiters: ['[[', ']]'],
  template: '#user-change-template',
  data() {
    return {
      users: [],
      showUsers: false,
      username: '',
    };
  },
  methods: {
    updateUser(user) {
      api.patch(`users/${user.id}/`, { username: user.username }).then(() => {
        this.store.displayMessage("Du kannst dir gar nicht vorstellen, wie dolle sich " + user.username + " freuen wird!", "warning");
      });
    },
    addUser() {
      api.post('users/', { username: this.username }).then(() => {
        this.username = ''
        this.loadUsers()
      })
    },
    loadUsers() {
      api.get('users/').then(response => {
        this.users = response.data
      })
    }
  },
  mounted() {
    this.loadUsers()
  }
};

export default UserChange;
