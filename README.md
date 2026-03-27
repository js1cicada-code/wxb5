# 微信H5应用

一个基于 Webpack 构建的微信H5应用项目模板。

## 功能特性

- 📦 使用 Webpack 5 打包
- 🔧 Babel 转译支持
- 🎨 CSS 提取和压缩
- 📱 移动端适配
- 🚀 开发服务器热更新
- 💡 jQuery + Axios 请求封装

## 目录结构

```
wxingbaoh5/
├── src/
│   ├── js/
│   │   └── index.js      # 入口文件
│   ├── css/
│   │   └── index.css     # 样式文件
│   └── images/           # 图片资源
├── index.html           # HTML 模板
├── webpack.config.js    # Webpack 配置
├── package.json         # 项目配置
└── README.md           # 说明文档
```

## 快速开始

### 安装依赖

```bash
npm install
```

### 开发模式

启动开发服务器，支持热更新：

```bash
npm run dev
```

访问 http://localhost:8080

### 生产构建

打包生产环境代码：

```bash
npm run build
```

输出目录：`dist/`

### 代码检查

```bash
npm run lint
```

## 技术栈

- **构建工具**: Webpack 5
- **JavaScript**: ES6+ (Babel 转译)
- **CSS**: CSS3 + PostCSS
- **HTTP库**: Axios
- **DOM操作**: jQuery

## 微信环境检测

项目内置微信环境检测功能：

```javascript
// 检测是否在微信浏览器中
const isWechat = app.checkWechat();
```

## 常用方法

### 显示提示

```javascript
app.showToast('操作成功', 2000);
```

### 显示/隐藏加载

```javascript
app.showLoading();
// ... 执行操作
app.hideLoading();
```

### HTTP 请求

```javascript
import { http } from './js/index';

// GET 请求
http.get('/api/data').then(res => {
  console.log(res);
});

// POST 请求
http.post('/api/data', { name: 'test' }).then(res => {
  console.log(res);
});
```

## 注意事项

1. 在微信环境中使用时，请确保已引入微信 JS-SDK
2. 生产环境请配置正确的 API 地址
3. 建议使用 HTTPS 协议

## License

MIT