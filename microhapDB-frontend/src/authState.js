// src/authState.js
import { reactive } from 'vue';

export const authState = reactive({
  isAuthenticated: false,
  isAdmin: false,
  username: null
});
