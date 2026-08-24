import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export interface History {
  id: number;
  type: string;
  question: string;
  answer: string;
  session_id?: string;
  tokens_used?: number;
  duration?: number;
  created_at: string;
  updated_at?: string;
}

export interface Report {
  id: number;
  title: string;
  type: string;
  content: string;
  data?: object;
  share_code?: string;
  created_at: string;
}

// 创建axios实例
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器 - 添加token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器 - 处理错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token过期，清除本地存储
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// 认证相关
export const authApi = {
  register: (data: { username: string; password: string; email?: string; nickname?: string }) =>
    api.post('/auth/register', data),
  
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }),
  
  getMe: () => api.get('/auth/me'),
  
  updateMe: (data: { nickname?: string; email?: string; avatar?: string }) =>
    api.put('/auth/me', data),
  
  changePassword: (oldPassword: string, newPassword: string) =>
    api.post('/auth/change-password', { old_password: oldPassword, new_password: newPassword }),
  
  getVipStatus: () => api.get('/auth/vip/status'),
  
  upgradeVip: (level: string) =>
    api.post('/auth/vip/upgrade', { level }),
};

// 历史记录相关
export const historyApi = {
  getHistories: (params?: { type?: string; search?: string; page?: number; page_size?: number }) =>
    api.get('/histories', { params }),
  
  getHistory: (id: number) => api.get(`/histories/${id}`),
  
  createHistory: (data: {
    type: string;
    question: string;
    answer: string;
    session_id?: string;
    tokens_used?: number;
    duration?: number;
  }) => api.post('/histories', data),
  
  deleteHistory: (id: number) => api.delete(`/histories/${id}`),
  
  getStats: () => api.get('/histories/stats/overview'),
};

// 报告相关
export const reportApi = {
  getReports: (params?: { type?: string; page?: number; page_size?: number }) =>
    api.get('/reports', { params }),
  
  getReport: (id: number) => api.get(`/reports/${id}`),
  
  createReport: (data: {
    title: string;
    type: string;
    content: string;
    data?: object;
  }) => api.post('/reports', data),
  
  deleteReport: (id: number) => api.delete(`/reports/${id}`),
  
  generateShareCode: (id: number) =>
    api.post(`/reports/${id}/share`),
  
  getSharedReport: (shareCode: string) =>
    api.get(`/share/${shareCode}`),
};

// 其他功能
export const miscApi = {
  uploadFile: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  
  getUploads: (params?: { page?: number; page_size?: number }) =>
    api.get('/uploads', { params }),
  
  createFeedback: (data: {
    type: string;
    content: string;
    rating?: number;
    contact_email?: string;
  }) => api.post('/feedback', data),
  
  getMyFeedback: (params?: { page?: number; page_size?: number }) =>
    api.get('/feedback/my', { params }),
  
  getReviews: (params?: { page?: number; page_size?: number }) =>
    api.get('/reviews', { params }),
  
  createReview: (data: { content: string; rating: number }) =>
    api.post('/reviews', data),
  
  likeReview: (id: number) =>
    api.post(`/reviews/${id}/like`),
  
  getTutorials: (params?: { type?: string }) =>
    api.get('/tutorials', { params }),
  
  getTutorial: (id: number) =>
    api.get(`/tutorials/${id}`),
};

export default api;
