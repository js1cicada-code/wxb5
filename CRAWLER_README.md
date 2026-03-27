# 北京单场数据爬虫使用说明

## 快速启动

### 方式1：分开运行（推荐）

终端1 - 启动爬虫：
```bash
python3 bjdc_crawler.py
```

终端2 - 启动前端服务：
```bash
npm run dev
```

### 方式2：同时启动
```bash
npm run start
```

### 方式3：使用脚本
```bash
chmod +x start_crawler.sh
./start_crawler.sh
```

## 数据说明

- 爬虫每5分钟自动更新一次数据
- 数据保存在 `dist/bjdc_data.json`
- 前端自动从JSON文件读取最新数据

## 访问地址

- 竞彩足球: http://localhost:8082/
- 竞彩篮球: http://localhost:8082/basketball.html
- 北京单场: http://localhost:8082/bjdc.html

## 爬虫功能

1. 获取期号列表
2. 获取比赛数据
3. 解析赔率信息
4. 自动保存JSON数据

## 注意事项

- 确保网络可访问 500.com
- 建议使用代理或VPN提高稳定性
- 数据仅供学习参考