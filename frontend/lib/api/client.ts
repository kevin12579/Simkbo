import axios from "axios";

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error("API 에러:", error.response.data);
    } else if (error.request) {
      console.error("네트워크 오류 — 서버에 연결할 수 없습니다.");
    }
    return Promise.reject(error);
  }
);

export default apiClient;
