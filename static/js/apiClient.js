// API客户端模块 - 统一管理所有后端API调用
const ApiClient = {
    // 通用请求方法
    async _request(endpoint, options = {}, retries = 2) {
    const defaultOptions = {
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        timeout: 10000 // 10秒超时
    };
    
    const mergedOptions = { ...defaultOptions, ...options };
    
    for (let attempt = 0; attempt <= retries; attempt++) {
        try {
            // 添加超时控制
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), mergedOptions.timeout);
            
            const response = await fetch(endpoint, {
                ...mergedOptions,
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            const data = await response.json();
            
            return {
                ok: response.ok,
                status: response.status,
                data: data,
                response: response,
                retried: attempt > 0
            };
            
        } catch (error) {
            console.error(`API请求失败 (${endpoint}), 尝试 ${attempt + 1}/${retries + 1}:`, error);
            
            // 如果是最后一次尝试，或者错误类型不应该重试，则抛出
            if (attempt === retries || error.name === 'AbortError') {
                return {
                    ok: false,
                    status: 0,
                    data: { 
                        status: 'error', 
                        message: error.name === 'AbortError' ? '请求超时' : '网络连接失败'
                    },
                    error: error
                };
            }
            
            // 等待一段时间后重试（指数退避）
            await this._delay(Math.pow(2, attempt) * 1000);
        }
    }
},

// 辅助函数：延迟
_delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
},
    
    // 提交记录
    async createSubmission(formData) {
        return this._request('/api/submission', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
    },
    
    // 获取所有记录
    async getSubmissions() {
        return this._request('/api/submissions');
    },
    
    // 删除记录
    async deleteSubmission(id) {
        return this._request(`/api/submission/${id}`, {
            method: 'DELETE'
        });
    },
    
    // 获取当前用户信息（为未来功能预留）
    async getCurrentUser() {
        return this._request('/api/user/current');
    }
};

// 导出为全局变量（简单方式，适合当前项目）
window.ApiClient = ApiClient;

// 错误处理器
const ErrorHandler = {
    // 根据错误类型返回用户友好的消息
    getFriendlyMessage(errorResult) {
        const { status, data } = errorResult;
        
        if (status === 0) {
            return '网络连接失败，请检查您的网络连接';
        }
        
        if (status === 401) {
            return '登录已过期，请重新登录';
        }
        
        if (status === 403) {
            return '权限不足，无法执行此操作';
        }
        
        if (status === 404) {
            return '请求的资源不存在';
        }
        
        if (status >= 500) {
            return '服务器内部错误，请稍后重试';
        }
        
        // 尝试使用后端返回的错误消息
        if (data && data.message) {
            return data.message;
        }
        
        return '操作失败，请稍后重试';
    },
    
    // 显示错误通知
    showError(message, duration = 5000) {
        this._showNotification(message, 'error', duration);
    },
    
    // 显示成功通知
    showSuccess(message, duration = 3000) {
        this._showNotification(message, 'success', duration);
    },
    
    // 私有方法：创建通知元素
    _showNotification(message, type, duration) {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // 添加到页面
        document.body.appendChild(notification);
        
        // 显示动画
        setTimeout(() => notification.classList.add('show'), 10);
        
        // 自动消失
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, duration);
    }
};

// 导出错误处理器
window.ErrorHandler = ErrorHandler;