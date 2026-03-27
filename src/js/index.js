/**
 * 微信H5应用入口文件
 */
import '../css/index.css';
import '../css/lottery-ui.css';
import '../css/lottery-pc.css';
import $ from 'jquery';
import axios from 'axios';

// 应用配置
const APP_CONFIG = {
  baseUrl: '',
  timeout: 10000
};

// 初始化 axios
const http = axios.create({
  baseURL: APP_CONFIG.baseUrl,
  timeout: APP_CONFIG.timeout
});

// 请求拦截器
http.interceptors.request.use(
  config => {
    // 可以在这里添加 token 等认证信息
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// 响应拦截器
http.interceptors.response.use(
  response => {
    return response.data;
  },
  error => {
    console.error('请求错误:', error);
    return Promise.reject(error);
  }
);

// 应用初始化
class App {
  constructor() {
    this.init();
  }

  init() {
    $(document).ready(() => {
      console.log('微信H5应用已初始化');
      this.bindEvents();
      this.checkWechat();
    });
  }

  // 绑定事件
  bindEvents() {
    // 示例：点击事件
    $(document).on('click', '.btn-action', (e) => {
      e.preventDefault();
      this.handleAction($(e.currentTarget));
    });
  }

  // 检查微信环境
  checkWechat() {
    const ua = navigator.userAgent.toLowerCase();
    const isWechat = ua.indexOf('micromessenger') !== -1;
    
    if (isWechat) {
      console.log('当前为微信环境');
      document.body.classList.add('wechat-env');
    } else {
      console.log('当前非微信环境');
      document.body.classList.add('non-wechat-env');
    }
    
    return isWechat;
  }

  // 处理操作
  handleAction($btn) {
    const action = $btn.data('action');
    console.log('执行操作:', action);
  }

  // 显示加载
  showLoading() {
    $('body').addClass('loading');
  }

  // 隐藏加载
  hideLoading() {
    $('body').removeClass('loading');
  }

  // 显示提示
  showToast(message, duration = 2000) {
    const $toast = $(`<div class="toast">${message}</div>`);
    $('body').append($toast);
    
    setTimeout(() => {
      $toast.addClass('show');
    }, 10);
    
    setTimeout(() => {
      $toast.removeClass('show');
      setTimeout(() => {
        $toast.remove();
      }, 300);
    }, duration);
  }
}

// 启动应用
window.app = new App();

// 导出模块
export { App, http };