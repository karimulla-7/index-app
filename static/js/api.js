/**
 * Index Client REST API Client
 * Clean asynchronous HTTP abstraction layer.
 */

const API = {
  // Base configuration
  baseUrl: '',

  async request(endpoint, options = {}) {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, options);
      if (!response.ok) {
        let errData = {};
        try {
          errData = await response.json();
        } catch (_) {}
        const errorMsg = errData.detail || `Request failed with status ${response.status}`;
        throw new Error(errorMsg);
      }
      return await response.json();
    } catch (err) {
      console.error(`[API Error] ${endpoint}:`, err);
      throw err;
    }
  },

  // Files
  async getFiles({ folderId = null, tag = null, search = null, sortBy = 'newest' } = {}) {
    const params = new URLSearchParams();
    if (folderId !== null && folderId !== undefined) params.append('folder_id', folderId);
    if (tag) params.append('tag', tag);
    if (search) params.append('search', search);
    if (sortBy) params.append('sort_by', sortBy);

    const queryStr = params.toString() ? `?${params.toString()}` : '';
    return this.request(`/api/files${queryStr}`);
  },

  async getFileDetails(fileId) {
    return this.request(`/api/files/${fileId}`);
  },

  async uploadFiles(fileList, folderId = null) {
    const formData = new FormData();
    for (let i = 0; i < fileList.length; i++) {
      formData.append('files', fileList[i]);
    }
    if (folderId) {
      formData.append('folder_id', folderId);
    }
    return this.request('/api/files/upload', {
      method: 'POST',
      body: formData
    });
  },

  async deleteFile(fileId) {
    return this.request(`/api/files/${fileId}`, {
      method: 'DELETE'
    });
  },

  async updateFolderAssignment(fileId, folderId) {
    return this.request(`/api/files/${fileId}/folder`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ folder_id: folderId })
    });
  },

  async addTag(fileId, tagName) {
    return this.request(`/api/files/${fileId}/tags`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tag_name: tagName })
    });
  },

  async removeTag(fileId, tagId) {
    return this.request(`/api/files/${fileId}/tags/${tagId}`, {
      method: 'DELETE'
    });
  },

  async reprocessAi(fileId) {
    return this.request(`/api/files/${fileId}/reprocess-ai`, {
      method: 'POST'
    });
  },

  // Folders
  async getFolders() {
    return this.request('/api/folders');
  },

  async createFolder(name, description = '', color = '#C09543', icon = 'folder') {
    return this.request('/api/folders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description, color, icon })
    });
  },

  async deleteFolder(folderId) {
    return this.request(`/api/folders/${folderId}`, {
      method: 'DELETE'
    });
  },

  // Tags
  async getTags() {
    return this.request('/api/tags');
  },

  // Search
  async askSearch(query) {
    return this.request('/api/search/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
  },

  // Chat
  async getChatHistory(fileId) {
    return this.request(`/api/chat/${fileId}/history`);
  },

  async sendChatMessage(fileId, message) {
    return this.request(`/api/chat/${fileId}/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });
  },

  async clearChatHistory(fileId) {
    return this.request(`/api/chat/${fileId}/history`, {
      method: 'DELETE'
    });
  },

  // System
  async getSystemStatus() {
    return this.request('/api/system/status');
  }
};
