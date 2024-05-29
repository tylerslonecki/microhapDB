import { reactive } from 'vue';

const state = reactive({
  isAuthenticated: !!localStorage.getItem('access_token'),
  isAdmin: JSON.parse(localStorage.getItem('is_admin')) || false,
});

const methods = {
  login(accessToken, isAdmin) {
    state.isAuthenticated = true;
    state.isAdmin = isAdmin;
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('is_admin', JSON.stringify(isAdmin));
  },
  logout() {
    state.isAuthenticated = false;
    state.isAdmin = false;
    localStorage.removeItem('access_token');
    localStorage.removeItem('is_admin');
  },
};

export default {
  state,
  methods,
};
