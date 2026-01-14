# Git 推送问题排查指南

## 问题1：私有仓库认证失败（Repository not found）

如果遇到以下错误：
```
remote: Repository not found.
fatal: repository 'https://github.com/icycola/make_ppt.git/' not found
```

**这通常是因为：**
- ✅ 仓库是私有的，但 Git 没有正确的认证信息
- ❌ 仓库不存在或已被删除
- ❌ 没有访问该仓库的权限

### 解决方案（按推荐顺序）

#### 方案1：使用 Personal Access Token (PAT) - 推荐 ⭐

GitHub 已不再支持使用密码进行 HTTPS 认证，必须使用 Personal Access Token：

1. **创建 Personal Access Token**：
   - 访问：https://github.com/settings/tokens
   - 点击 "Generate new token" → "Generate new token (classic)"
   - 设置名称（如：`git-push-token`）
   - 选择权限：至少勾选 `repo`（完整仓库访问权限）
   - 设置过期时间
   - 点击 "Generate token"
   - **重要**：复制生成的 token（只显示一次！）

2. **使用 Token 推送**：
   ```powershell
   # 方式A：在 URL 中包含 token（一次性使用）
   git push https://你的token@github.com/icycola/make_ppt.git main
   
   # 方式B：更新远程 URL 包含 token（永久保存）
   git remote set-url origin https://你的token@github.com/icycola/make_ppt.git
   git push -u origin main
   
   # 方式C：使用 Git Credential Manager（推荐，更安全）
   # 推送时会提示输入用户名和密码，用户名填你的 GitHub 用户名，密码填 token
   git push -u origin main
   ```

3. **配置 Git Credential Manager（Windows）**：
   ```powershell
   # 配置 Git 使用 Windows Credential Manager
   git config --global credential.helper manager-core
   
   # 然后正常推送，会弹出 Windows 凭据窗口
   git push -u origin main
   # 用户名：你的 GitHub 用户名
   # 密码：粘贴你的 Personal Access Token
   ```

#### 方案2：使用 SSH 方式（最安全）⭐

SSH 方式不需要每次输入密码，更安全方便：

1. **检查是否已有 SSH 密钥**：
   ```powershell
   ls ~/.ssh
   # 查看是否有 id_rsa 或 id_ed25519 文件
   ```

2. **如果没有，生成 SSH 密钥**：
   ```powershell
   ssh-keygen -t ed25519 -C "1178419733@qq.com"
   # 按 Enter 使用默认路径
   # 可以设置密码或直接按 Enter（不设置密码）
   ```

3. **添加 SSH 密钥到 GitHub**：
   ```powershell
   # 复制公钥内容
   cat ~/.ssh/id_ed25519.pub
   # 或者
   Get-Content ~/.ssh/id_ed25519.pub
   ```
   - 访问：https://github.com/settings/keys
   - 点击 "New SSH key"
   - 粘贴公钥内容
   - 保存

4. **测试 SSH 连接**：
   ```powershell
   ssh -T git@github.com
   # 应该看到：Hi icycola! You've successfully authenticated...
   ```

5. **切换到 SSH 方式**：
   ```powershell
   # 移除现有的 HTTPS 远程仓库
   git remote remove origin
   
   # 添加 SSH 方式的远程仓库
   git remote add origin git@github.com:icycola/make_ppt.git
   
   # 推送到远程
   git push -u origin main
   ```

#### 方案3：使用 GitHub CLI（最简单）

```powershell
# 1. 安装 GitHub CLI（如果未安装）
# 下载：https://cli.github.com/

# 2. 登录 GitHub
gh auth login
# 选择 GitHub.com
# 选择 HTTPS 或 SSH
# 按照提示完成认证

# 3. 如果仓库不存在，创建并推送
gh repo create make_ppt --private --source=. --remote=origin --push

# 4. 如果仓库已存在，直接推送
git push -u origin main
```

---

## 问题2：无法连接到 GitHub

如果遇到以下错误：
```
fatal: unable to access 'https://github.com/icycola/make_ppt.git/': Failed to connect to github.com port 443
```

## 解决方案

### 方案1：先完成本地提交（推荐）

即使无法推送到远程，你也可以先完成本地提交，稍后再推送：

```powershell
# 1. 确保所有文件已添加
git status

# 2. 完成本地提交
git commit -m "Initial commit: Add backend and frontend modules"

# 3. 查看提交历史
git log --oneline

# 稍后网络恢复后再推送
git push -u origin main
```

### 方案2：使用 SSH 方式（如果已配置 SSH 密钥）

```powershell
# 1. 移除现有的 HTTPS 远程仓库
git remote remove origin

# 2. 添加 SSH 方式的远程仓库
git remote add origin git@github.com:icycola/make_ppt.git

# 3. 推送到远程
git push -u origin main
```

### 方案3：配置代理（如果你使用代理）

```powershell
# 设置 HTTP 代理（替换为你的代理地址和端口）
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890

# 或者使用 SOCKS5 代理
git config --global http.proxy socks5://127.0.0.1:7890
git config --global https.proxy socks5://127.0.0.1:7890

# 推送到远程
git push -u origin main

# 如果不再需要代理，可以取消设置
# git config --global --unset http.proxy
# git config --global --unset https.proxy
```

### 方案4：使用 GitHub CLI（gh）

```powershell
# 安装 GitHub CLI 后
gh auth login
gh repo create make_ppt --private --source=. --remote=origin --push
```

### 方案5：检查网络和防火墙

1. **检查网络连接**：
   ```powershell
   ping github.com
   ```

2. **检查防火墙设置**：确保防火墙没有阻止 Git 访问 GitHub

3. **尝试使用移动热点**：如果当前网络有问题，可以尝试切换网络

### 方案6：使用镜像站点（如果在中国大陆）

如果在中国大陆，可以尝试使用 GitHub 镜像或 Gitee：

#### 使用 Gitee（码云）

```powershell
# 1. 在 Gitee 上创建仓库
# 2. 添加 Gitee 远程仓库
git remote add gitee https://gitee.com/你的用户名/make_ppt.git

# 3. 推送到 Gitee
git push -u gitee main
```

## 当前状态检查

运行以下命令检查当前 Git 状态：

```powershell
# 检查远程仓库配置
git remote -v

# 检查提交状态
git status

# 查看提交历史
git log --oneline
```

## 推荐操作流程

1. **先完成本地提交**（不依赖网络）：
   ```powershell
   git commit -m "Initial commit: Add backend and frontend modules"
   ```

2. **验证本地提交成功**：
   ```powershell
   git log --oneline
   ```

3. **稍后网络恢复或找到解决方案后再推送**：
   ```powershell
   git push -u origin main
   ```

## 注意事项

- 本地 Git 仓库已经创建，所有代码更改都会保存在本地
- 即使无法推送到远程，你的代码也是安全的
- 可以随时在本地进行提交、分支管理等操作
- 推送只是将本地代码同步到远程服务器，不是必需的

---

## 协作与权限管理：如何让别人访问私有仓库

### ❌ 不推荐：直接分享 Personal Access Token

**不要**直接把自己的 Personal Access Token 给别人，因为：
- Token 拥有你账户的完整权限（取决于创建时的权限设置）
- 无法单独撤销某个人的访问权限
- 如果泄露，可能被恶意使用
- 无法追踪是谁在使用

### ✅ 推荐方案1：添加协作者（Collaborator）- 最推荐 ⭐⭐⭐

这是最安全和推荐的方式：

#### 步骤1：添加协作者到仓库

1. **进入仓库设置**：
   - 访问：https://github.com/icycola5556/make_ppt/settings/access
   - 或者：仓库页面 → Settings → Collaborators

2. **添加协作者**：
   - 点击 "Add people"
   - 输入对方的 GitHub 用户名或邮箱
   - 选择权限级别：
     - **Read**：只能拉取代码
     - **Write**：可以推送代码（推荐）
     - **Admin**：可以管理仓库设置（谨慎使用）

3. **发送邀请**：
   - 对方会收到邮件邀请
   - 对方接受邀请后即可访问仓库

#### 步骤2：协作者配置自己的认证

协作者需要在自己的电脑上配置认证（二选一）：

**方式A：使用 Personal Access Token（协作者自己的）**
```powershell
# 协作者需要：
# 1. 创建自己的 PAT：https://github.com/settings/tokens
# 2. 配置 Git 凭据管理器
git config --global credential.helper manager

# 3. 克隆仓库
git clone https://github.com/icycola5556/make_ppt.git

# 4. 推送时会提示输入：
#    用户名：协作者的 GitHub 用户名
#    密码：协作者自己的 PAT（不是你的！）
```

**方式B：使用 SSH（推荐）**
```powershell
# 协作者需要：
# 1. 生成自己的 SSH 密钥
ssh-keygen -t ed25519 -C "协作者的邮箱"

# 2. 添加 SSH 公钥到自己的 GitHub 账户
#    访问：https://github.com/settings/keys

# 3. 使用 SSH 克隆
git clone git@github.com:icycola5556/make_ppt.git
```

### ✅ 推荐方案2：使用 GitHub Teams（适合团队）

如果有多个人需要访问：

1. **创建团队**：
   - 访问：https://github.com/organizations/你的组织名/teams/new
   - 或者：Settings → Teams → New team

2. **添加成员到团队**：
   - 添加需要访问的成员

3. **给团队分配仓库权限**：
   - 在仓库的 Settings → Collaborators & teams
   - 添加团队并设置权限

### ✅ 推荐方案3：使用 Deploy Keys（只读访问）

如果只需要给某个服务器/CI 系统只读访问：

1. **生成 SSH 密钥对**（在服务器上）：
   ```bash
   ssh-keygen -t ed25519 -C "deploy-key"
   ```

2. **添加 Deploy Key**：
   - 仓库 Settings → Deploy keys → Add deploy key
   - 粘贴公钥内容
   - 勾选 "Allow write access"（如果需要推送）

3. **在服务器上配置**：
   ```bash
   git clone git@github.com:icycola5556/make_ppt.git
   ```

### 权限级别说明

| 权限 | 可以做什么 | 适用场景 |
|------|-----------|---------|
| **Read** | 拉取代码、查看 Issues/PR | 只读访问，查看代码 |
| **Write** | 推送代码、创建分支、提交 PR | 普通开发者（推荐） |
| **Admin** | 管理设置、删除仓库 | 项目维护者 |

### 撤销访问权限

如果需要移除某个人的访问：

1. 访问：https://github.com/icycola5556/make_ppt/settings/access
2. 找到要移除的协作者
3. 点击 "Remove" 或 "Change role" → "Remove access"

**注意**：移除后，对方无法再访问仓库，但已经克隆到本地的代码仍然存在。

### 最佳实践总结

1. ✅ **使用协作者功能**，不要分享自己的 Token
2. ✅ **给最小必要权限**（通常 Write 就够了）
3. ✅ **定期审查**协作者列表，移除不再需要的人
4. ✅ **使用 SSH** 而不是 HTTPS（更安全方便）
5. ✅ **为 CI/CD 使用 Deploy Keys**，而不是个人 Token
6. ❌ **不要**在代码中硬编码 Token
7. ❌ **不要**在公开的地方分享 Token

---

## 常见问题

### Q: 协作者需要我给他 Token 吗？
**A:** 不需要！协作者需要创建自己的 Personal Access Token，或者使用 SSH 密钥。

### Q: 如何知道谁在访问我的仓库？
**A:** 在仓库的 Insights → Traffic 可以查看访问统计。Settings → Collaborators 可以看到所有协作者。

### Q: 协作者可以删除我的仓库吗？
**A:** 只有 Admin 权限的协作者可以删除仓库。Write 权限只能推送代码，不能删除仓库。

### Q: 如果协作者泄露了代码怎么办？
**A:** 立即移除他的访问权限，并考虑更换敏感信息（如 API 密钥）。
