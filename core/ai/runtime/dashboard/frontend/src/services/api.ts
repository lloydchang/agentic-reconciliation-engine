import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8081';

class ApiService {
  private baseURL = `${API_BASE_URL}/api`;

  // Agent Management
  async getAgents() {
    const response = await axios.get(`${this.baseURL}/agents`);
    return response.data;
  }

  async getAgent(id: string) {
    const response = await axios.get(`${this.baseURL}/agents/${id}`);
    return response.data;
  }

  async startAgent(id: string) {
    const response = await axios.post(`${this.baseURL}/agents/${id}/start`);
    return response.data;
  }

  async stopAgent(id: string) {
    const response = await axios.post(`${this.baseURL}/agents/${id}/stop`);
    return response.data;
  }

  async restartAgent(id: string) {
    const response = await axios.post(`${this.baseURL}/agents/${id}/restart`);
    return response.data;
  }

  // Skills Management
  async getSkills() {
    const response = await axios.get(`${this.baseURL}/skills`);
    return response.data;
  }

  async getSkill(id: string) {
    const response = await axios.get(`${this.baseURL}/skills/${id}`);
    return response.data;
  }

  async executeSkill(id: string, params: any) {
    const response = await axios.post(`${this.baseURL}/skills/${id}/execute`, params);
    return response.data;
  }

  // System APIs
  async getSystemStatus() {
    const response = await axios.get(`${this.baseURL}/system/status`);
    return response.data;
  }

  async getSystemMetrics() {
    const response = await axios.get(`${this.baseURL}/system/metrics`);
    return response.data;
  }

  async getHealth() {
    const response = await axios.get(`${this.baseURL}/system/health`);
    return response.data;
  }

  // Activity APIs
  async getActivities(limit: number = 50) {
    const response = await axios.get(`${this.baseURL}/activity?limit=${limit}`);
    return response.data;
  }
}

export default ApiService;
