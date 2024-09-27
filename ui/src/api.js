import axios from "axios";

class APIClient {
  updateMessage(message) {
    return axios.put(`/api/messages/${message.id}`, message);
  }

  accept_message(message, update_text) {
    return axios.post(
      `/api/messages/${message.user}/accept/${message.id}`,
      update_text,
    );
  }

  reject_message(message) {
    return axios.post(`/api/messages/${message.user}/reject/${message.id}`);
  }

  me() {
    return axios.get("/api/me");
  }

  user_list() {
    return axios.get("/api/users");
  }

  user_create(user) {
    return axios.post("/api/users", user);
  }

  user_auth_code(user) {
    return axios.post(`/api/users/${user.name}/auth-code`);
  }

  password_login(credentials) {
    return axios.post("/auth/login", credentials);
  }

  code_login(credentials) {
    return axios.post("/auth/auth-code", credentials);
  }

  logout() {
    return axios.post("/auth/logout");
  }

  get_recent_messages() {
    return axios.get("/api/recent-messages");
  }

  clear_recent_messages() {
    return axios.delete("/api/recent-messages");
  }

  get_translations(language) {
    return axios.get(`/translations/${language}`);
  }
}

export default APIClient;
