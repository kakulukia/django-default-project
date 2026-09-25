// store.js
const { defineStore } = Pinia;

export const useAppStore = defineStore('app', {
  state: () => ({
    notifications: [],
    user: null,
    userQueryDone: false,
  }),
  actions: {
    displayMessage(message, type = 'info', action='') {
      // 'success' | 'info' | 'warning' | 'error'
      this.notifications.push({
        message: message,
        type,
        timestamp: new Date(),
        action,
      })
    },
    displayError(message, action='') {
      this.displayMessage(message, 'error', action)
    },
    displaySuccess(message, action='') {
      this.displayMessage(message, 'success', action)
    },
    removeOldNotifications() {
      setInterval(() => {
        const now = new Date();
        this.notifications = this.notifications.filter(
          notification => (now - notification.timestamp) < 5000
        );
      }, 1000);
    },
  }
});
