# Railway部署步骤

## 1. 推送代码到Railway

### 方法A：通过GitHub连接
1. 确保你的代码已经推送到GitHub
2. 访问 [Railway](https://railway.app)
3. 点击 "New Project"
4. 选择 "Deploy from GitHub repo"
5. 选择你的YouTube to MP3项目
6. Railway会自动检测并部署

### 方法B：通过Railway CLI
```bash
# 安装Railway CLI
npm install -g @railway/cli

# 登录Railway
railway login

# 初始化项目
railway init

# 部署
railway up
```

## 2. 获取部署URL

部署完成后，Railway会提供一个URL，格式类似：
```
https://your-project-name.up.railway.app
```

## 3. 更新前端API配置

在 `script.js` 中，将以下行：
```javascript
: 'https://your-railway-project.up.railway.app/api'; // 请替换为你的Railway项目域名
```

替换为你的实际Railway URL，例如：
```javascript
: 'https://yt2mp3-converter.up.railway.app/api';
```

## 4. 配置环境变量（可选）

在Railway项目设置中，可以添加环境变量：
- `FLASK_ENV=production`
- `PORT=5000` (Railway通常自动设置)

## 5. 测试部署

1. 访问你的Railway URL
2. 测试API端点：
   - `GET /api/health` - 健康检查
   - `GET /api/network-test` - 网络测试

## 6. 更新GitHub Pages

确保你的GitHub Pages使用的是更新后的代码：
```bash
git add .
git commit -m "Update API URL for Railway deployment"
git push origin main
```

## 故障排除

### 1. 构建失败
- 检查 `requirements.txt` 是否包含所有依赖
- 确保Python版本兼容

### 2. 运行时错误
- 检查Railway日志：`railway logs`
- 确保端口配置正确

### 3. CORS错误
- 确保后端CORS配置包含你的GitHub Pages域名
- 检查API URL是否正确

### 4. FFmpeg问题
Railway会自动安装FFmpeg，但如果遇到问题，可以在项目中添加：
```bash
# 在项目根目录创建 nixpacks.toml
[phases.setup]
nixPkgs = ["python39", "ffmpeg"]
```

## 监控和维护

- 使用Railway仪表板监控应用状态
- 定期检查日志
- 监控资源使用情况

完成这些步骤后，你的YouTube to MP3转换器应该能够在GitHub Pages上正常工作！ 