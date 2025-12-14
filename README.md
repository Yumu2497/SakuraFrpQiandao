# SakuraFrp 自动签到脚本

使用 AI 视觉识别自动完成 SakuraFrp 的验证码签到。

## 功能特性

- ✅ 自动登录 SakuraFrp 账户
- ✅ AI 视觉识别九宫格验证码
- ✅ 智能点击匹配的验证码格子
- ✅ 失败自动重试（最多3次）
- ✅ 支持 GitHub Actions 定时执行
- ✅ 详细的日志记录

## 本地运行

### 1. 环境准备

```bash
# 克隆项目
git clone <your-repo-url>
cd SakuraFrpQiandao

# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
# SakuraFrp 账户信息
SAKURAFRP_USER=your_username
SAKURAFRP_PASS=your_password

# AI 模型配置（支持 OpenAI 兼容的 API）
BASE_URL=https://api.example.com/v1
API_KEY=your_api_key
MODEL=your_model_name

# 最大重试次数 (可选)
MAX_RETRIES=默认为10

# Chrome 路径（可选）
CHROME_BINARY_PATH=

# 运行模式（可选）
HEADLESS=false
```

### 3. 下载 ChromeDriver

从 [ChromeDriver 官网](https://chromedriver.chromium.org/) 下载对应版本的 `chromedriver.exe`，放在项目根目录。

### 4. 运行脚本

```bash
python main.py
```

## GitHub Actions 部署

### 1. Fork 本项目

点击右上角 Fork 按钮，将项目 Fork 到你的账户。

### 2. 配置 Secrets

在你的 GitHub 仓库中：

1. 进入 `Settings` → `Secrets and variables` → `Actions`
2. 点击 `New repository secret` 添加以下密钥：

#### 必需配置

| 密钥名称 | 说明 | 示例 |
|---------|------|------|
| `SAKURAFRP_USER` | SakuraFrp 用户名 | `your_username` |
| `SAKURAFRP_PASS` | SakuraFrp 密码 | `your_password` |
| `BASE_URL` | AI API 地址 | `https://api.openai.com/v1` |
| `API_KEY` | AI API 密钥 | `sk-xxx...` |
| `MODEL` | 模型名称 | `gpt-4o` |

#### 邮件通知配置（可选）

| 密钥名称 | 说明 | 示例 | 是否必需 |
|---------|------|------|---------|
| `EMAIL_USERNAME` | 发件邮箱 | `your-email@gmail.com` | 是 |
| `EMAIL_PASSWORD` | 邮箱应用密码 | `abcd efgh ijkl mnop` | 是 |
| `RECEIVER_EMAIL` | 收件邮箱 | `notify@example.com` | 否（默认发给自己） |
| `SMTP_SERVER` | SMTP 服务器 | `smtp.gmail.com` | 否（默认 Gmail） |
| `SMTP_PORT` | SMTP 端口 | `587` | 否（默认 587） |

### 3. 启用 Actions

1. 进入 `Actions` 标签页
2. 点击 `I understand my workflows, go ahead and enable them`

### 4. 测试运行

- **手动触发**：进入 Actions → 选择工作流 → 点击 `Run workflow`
- **自动运行**：每天北京时间 9:00 自动执行

### 5. 查看结果

- 在 Actions 页面查看运行状态
- 点击具体的运行记录查看详细日志
- 下载 `checkin-logs` 查看完整日志文件
- **接收邮件通知**：每次运行后会自动发送日志邮件到你的邮箱

## 邮件通知配置

### Gmail 配置步骤

1. **开启两步验证**
   - 登录 Gmail → Google 账户设置
   - 安全性 → 两步验证（必须先开启）

2. **生成应用专用密码**
   - 两步验证 → 应用专用密码
   - 选择"邮件"和"其他"
   - 生成 16 位密码（格式：`abcd efgh ijkl mnop`）

3. **添加到 GitHub Secrets**
   - `EMAIL_USERNAME`: 你的 Gmail 地址
   - `EMAIL_PASSWORD`: 刚才生成的 16 位应用密码

### 其他邮箱配置

**QQ 邮箱**
```
SMTP_SERVER: smtp.qq.com
SMTP_PORT: 587 或 465
需要开启 SMTP 服务并获取授权码
```

**163 邮箱**
```
SMTP_SERVER: smtp.163.com
SMTP_PORT: 465
需要开启 SMTP 服务并获取授权码
```

**Outlook/Hotmail**
```
SMTP_SERVER: smtp-mail.outlook.com
SMTP_PORT: 587
使用账户密码即可
```

### 邮件内容

邮件会包含：
- ✅/❌ 签到状态（成功/失败）
- 📅 执行时间
- 📋 最近 2000 字符的日志摘要
- 📎 完整日志文件作为附件

### 禁用邮件通知

如果不需要邮件通知，只需不配置 `EMAIL_USERNAME` 和 `EMAIL_PASSWORD`，脚本会自动跳过邮件发送。

## 项目文件结构

```
SakuraFrp-Qiandao/
├── .github/
│   └── workflows/
│       └── checkin.yml          # GitHub Actions 工作流
├── debug_sakura.py              # 主签到脚本
├── send_email.py                # 邮件通知脚本
├── requirements.txt             # Python 依赖
├── .env                         # 本地环境变量（不上传）
├── .gitignore                   # Git 忽略规则
├── checkin.log                  # 运行日志（自动生成）
└── README.md                    # 项目说明
```

## 配置说明

### 定时任务时间

修改 `.github/workflows/checkin.yml` 中的 cron 表达式：

```yaml
schedule:
  - cron: '0 1 * * *'  # UTC 1:00 = 北京时间 9:00
```

常用时间对照：
- `0 1 * * *` - 每天 9:00（北京时间）
- `0 13 * * *` - 每天 21:00（北京时间）
- `0 1,13 * * *` - 每天 9:00 和 21:00

### AI 模型推荐

支持任何兼容 OpenAI API 的多模态模型：

- **OpenAI**: `gpt-4o`, `gpt-4-vision-preview`
- **阿里通义**: `qwen-vl-plus`, `qwen-vl-max`
- **智谱 AI**: `glm-4v`
- **ModelScope**: 各种开源视觉模型

### 重试次数

修改 `debug_sakura.py` 中的重试次数：

```python
self.max_retries = 3  # 最大重试次数
```

## 故障排查

### 问题：验证码识别失败

**原因**：AI 模型识别不准确

**解决方案**：
1. 尝试更换更强大的视觉模型
2. 优化 Prompt 提示词
3. 增加重试次数

### 问题：GitHub Actions 运行失败

**原因**：环境问题或依赖安装失败

**解决方案**：
1. 检查 Secrets 是否正确配置
2. 查看 Actions 日志中的具体错误
3. 确保 requirements.txt 中的依赖版本正确

### 问题：登录失败

**原因**：账号密码错误或网络问题

**解决方案**：
1. 验证 Secrets 中的用户名密码
2. 检查账号是否正常
3. 查看日志中的详细错误信息

### 问题：未收到邮件通知

**原因**：邮箱配置错误或 SMTP 服务未开启

**解决方案**：
1. 检查 `EMAIL_USERNAME` 和 `EMAIL_PASSWORD` 是否正确配置
2. 确认使用的是**应用专用密码**，不是登录密码
3. 检查邮箱是否开启了 SMTP 服务
4. 查看 Actions 日志中的邮件发送错误信息
5. 检查垃圾邮件文件夹

## 注意事项

⚠️ **重要提示**：

1. 请勿频繁触发 Actions，避免被限流
2. 妥善保管 API 密钥和邮箱密码，不要泄露
3. 定期检查签到日志或邮件，确保正常运行
4. 遵守 SakuraFrp 的服务条款
5. **邮箱应用密码不是登录密码**，Gmail 需要开启两步验证后生成应用专用密码
6. 邮件通知是可选的，不配置也不影响签到功能

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 相关链接

- [SakuraFrp 官网](https://www.natfrp.com/)
- [Selenium 文档](https://www.selenium.dev/documentation/)
- [GitHub Actions 文档](https://docs.github.com/en/actions)