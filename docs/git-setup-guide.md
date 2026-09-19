# Git / GitHub 上手操作手册（AutoGrader 项目）

> 面向本项目 B（前端 / 仓库管理）执行，A、C 可照第 1、5、7 步配置自己的开发环境。
> 假设项目目录为 `D:\projects\autograder`，请按实际情况替换路径。

---

## 第 1 步：检查 Git 环境

### 1.1 打开终端

在项目文件夹里右键 → 选择 **Open Git Bash here**（中文系统可能显示"Git Bash Here"）。

- 如果右键菜单里没有这一项：按 Win 键 → 搜索 `Git Bash` → 打开后敲 `cd /d/projects/autograder`（注意：Git Bash 里 D 盘写作 `/d/`，反斜杠要换成斜杠）
- 如果连 Git Bash 都搜不到 → Git 没装。去 `https://git-scm.com/download/win` 下载，一路默认下一步装完，再回来看 1.1

### 1.2 验证安装

```bash
git --version
```

- 成功：输出类似 `git version 2.43.0.windows.1`
- 失败：提示 `command not found` → 回到 1.1 重装

### 1.3 配置身份（只需一次，之后永久生效）

```bash
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"
```

- 名字用真名或团队内习惯的昵称，**不要用 `aaa`、`123`**，提交历史要让评委看得懂
- 邮箱建议用注册 GitHub 的那个邮箱，GitHub 才能把提交关联到你的账号
- 验证：`git config --global --list`，能回显上面两条即成功

---

## 第 2 步：本地初始化并首次提交

> 以下命令都在 Git Bash 里、且当前目录是项目根目录时执行。
> 用 `pwd` 命令可以查看当前所在目录，正确时应显示 `/d/projects/autograder`。

### 2.1 初始化仓库

```bash
git init
```

成功标志：出现 `Initialized empty Git repository in D:/projects/autograder/.git/`，文件夹里会多出一个 `.git` 隐藏目录。

### 2.2 统一主干分支名为 main

```bash
git branch -M main
```

（刚 init 完还没有提交，这一步不会报错，执行即可。）

### 2.3 暂存所有文件

```bash
git add .
```

### 2.4 检查暂存内容（关键一步，不要跳过）

```bash
git status
```

应该看到 8 个文件被列为 `new file`：

```
README.md
.gitignore
docs/api.md
docs/commit-convention.md
docs/requirements.md
frontend/README.md
backend/README.md
data/README.md
```

**必须确认没有**：`.env`、`node_modules/`、`*.db`、`dist/`。如果出现了敏感文件，执行 `git rm --cached 文件名` 取消暂存，并检查 `.gitignore` 是否覆盖。

### 2.5 提交

```bash
git commit -m "chore: 初始化项目骨架与协作规范"
```

成功标志：输出 `8 files changed` 之类的统计行。

### 2.6 查看提交历史

```bash
git log --oneline
```

应看到一条记录，形如 `a1b2c3d chore: 初始化项目骨架与协作规范`。

---

## 第 3 步：在 GitHub 创建远程仓库

### 3.1 登录并新建

1. 浏览器打开 `https://github.com` 并登录
2. 右上角 **+** → **New repository**
3. 填写表单：
   - **Repository name**：`autograder`
   - **Description**：`计算机实验报告智能评阅平台｜粤港澳大湾区 AI Coding 创新大赛`
   - **Public / Private**：选 **Private**（赛中先私有，赛后按要求开源）
   - **Add a README file**：不勾
   - **Add .gitignore**：不勾
   - **Choose a license**：不勾
4. 点绿色 **Create repository**

> 三个勾选项必须都不勾：本地已经有这些文件，勾了会造成远程仓库"非空"，推送时报 `rejected` 错误，还得额外处理。

### 3.2 复制仓库地址

建好后页面会跳到仓库主页，点绿色 **Code** 按钮 → 选 **HTTPS** → 复制形如下面的地址：

```
https://github.com/你的用户名/autograder.git
```

---

## 第 4 步：生成访问令牌（PAT）并推送

GitHub 从 2021 年起不再支持用账号密码推送，必须用 Personal Access Token 当密码。

### 4.1 生成 Token

1. GitHub 右上角头像 → **Settings**
2. 左侧栏最下 → **Developer settings**
3. **Personal access tokens** → **Tokens (classic)** → 右上 **Generate new token** → **Generate new token (classic)**
4. 填写：
   - **Note**：`autograder-push`
   - **Expiration**：`90 days`（够用完比赛）
   - **Select scopes**：勾选 **repo**（勾最上面那个总开关即可，子项会自动勾满）
5. 拉到底 → **Generate token**
6. 页面顶部出现一串 `ghp_` 开头的字符 → **立刻复制**，离开页面就再也看不到

### 4.2 关联远程仓库

```bash
git remote add origin https://github.com/你的用户名/autograder.git
```

> 把地址换成 3.2 复制的真实地址。填错了用 `git remote set-url origin 新地址` 修正，
> 用 `git remote -v` 可以查看当前配置。

### 4.3 推送

```bash
git push -u origin main
```

会弹出登录窗口（Git Credential Manager）：

- **账号**：GitHub 用户名
- **密码**：粘贴 4.1 生成的 PAT（不是你的登录密码）

成功标志：

```
* [new branch]      main -> main
branch 'main' set up to track 'origin/main'.
```

刷新 GitHub 页面，能看到 README 内容渲染出来了。

> 若提示 `Support for password authentication was removed` → 说明密码框里填的是登录密码，改填 PAT。
> 若提示 `remote origin already exists` → 执行 `git remote set-url origin 地址` 后再推。

---

## 第 5 步：邀请 A、C 加入协作

1. 进入仓库页 → **Settings**（注意是仓库的 Settings，不是账号的）
2. 左侧 **Collaborators** → 点 **Add people**
3. 输入 A 或 C 的 GitHub 用户名 / 注册邮箱 → 选中 → 发送邀请
4. 告诉两人：去邮箱点 **Accept invitation**，**必须点**，否则没有推送权限

没有 GitHub 账号的，让他们先注册（用户名建议用真名拼音，方便辨认）。

---

## 第 6 步：创建 dev 开发分支

```bash
git checkout -b dev
git push -u origin dev
```

之后日常开发都在 `dev` 上提交，功能验证通过后再合并回 `main`。
切换分支：`git checkout main` / `git checkout dev`。

---

## 第 7 步：验收（任务的完成标准）

让 A、C 各自执行一遍，两人都能推上去即验收通过：

```bash
git clone https://github.com/你的用户名/autograder.git
cd autograder
git config --global user.name "他的名字"
git config --global user.email "他的邮箱"
echo "test by A" > test.txt
git add .
git commit -m "chore: 测试推送权限"
git push
```

最后你在 GitHub 仓库页点 **Commits**，应能看到三条提交记录。

---

## 常见报错速查

| 报错信息 | 原因 | 解决 |
|---|---|---|
| `command not found: git` | 未安装 Git | 去 git-scm.com 安装 |
| `Support for password authentication was removed` | 密码处填了登录密码 | 改填 PAT |
| `remote origin already exists` | 重复添加远程 | `git remote set-url origin 地址` |
| `rejected - fetch first` | 远程仓库非空（建仓时勾了 README） | `git pull --rebase origin main` 后再 push |
| `Permission denied`（推送时） | 不是协作者 / 没接受邀请 | 检查 Collaborators 邀请是否已接受 |
| `Please tell me who you are` | 没配置 user.name / user.email | 回到 1.3 配置 |
| 推送一直卡住 / 超时 | 网络问题 | 换 Gitee 建仓，流程完全相同 |

---

## 附：日常提交流程（第 6 步之后每天都用）

```bash
git checkout dev          # 切到开发分支
git pull                  # 拉取队友最新代码，开工前必做
# ……写代码……
git status                # 看看改了哪些文件
git add .
git commit -m "feat: 完成报告上传页的拖拽上传与格式校验"
git push                  # 推到远程
```

提交信息规范见 [commit-convention.md](commit-convention.md)。
