// store.js
const { defineStore } = Pinia;

export const useAppStore = defineStore('app', {
  state: () => ({
    notifications: [],
    user: null,
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
    redirectToLogin() {
      window.location.href = '/admin/login/?next=' + window.location
    },
    removeOldNotifications() {
      const now = new Date()
      this.notifications = this.notifications.filter(notification => {
        const diff = now - notification.timestamp
        return diff < 3000 // keep notifications for 5 seconds
      })
      setTimeout(() => {
        this.removeOldNotifications()
      }, 1000)
    },
  }
});
