# 网络故障应对手册（GitHub 连接被重置）

> 适用症状：`fatal: unable to access 'https://github.com/...': Recv failure: Connection was reset`
> 或 `Failed to connect to github.com port 443`、推送卡住不动、`RPC failed`。

## 一、先搞清楚：这不是命令写错，也不是仓库坏了

`Connection was reset` 是**网络层**错误——TCP 握手成功了，但 HTTP 请求发到一半被中途掐断。
命令、凭据、仓库配置都没问题，**换任何写法都一样会失败**。

### 实测结论（2026-09-22，本项目所在网络）

| 测试项 | 结果 | 含义 |
|---|---|---|
| DNS 解析 github.com | `20.205.243.166` | 正常 |
| TCP 443 连续 5 次探测 | 4 成功 / 1 失败 | **间歇性**，约 20% 失败率 |
| `curl https://github.com`（网页） | 200，0.9s | 网页能开 |
| `curl` Git 端点 `/info/refs` 连续 4 次 | 1 次超时 / **3 次返回 401** | 401 = 打通了（只是需要认证），**重试就能过** |
| ssh.github.com:443 | 可达 | SSH 通道可用 |
| github.com:22 | 可达 | SSH 通道可用 |
| gitee.com | 200，通畅 | 国内通道稳定 |

**一句话：网络是间歇性抽风，同一秒重试几次就能成功。**

## 二、第一招：重试（成本 0，先做这个）

带自动重试的推送命令，失败就自动再试，最多 5 次：

```bash
for i in 1 2 3 4 5; do git push && break; echo "第 $i 次失败，3 秒后重试..."; sleep 3; done
```

拉取同理（GitHub 挂着时 `git pull` 也会被重置）：

```bash
for i in 1 2 3 4 5; do git pull && break; echo "第 $i 次失败，3 秒后重试..."; sleep 3; done
```

## 三、第二招：把 HTTP/2 降级为 HTTP/1.1（减少被重置概率）

HTTP/2 是多路复用，连接一被掐整批请求全废；降成 HTTP/1.1 后抗干扰明显变好：

```bash
git config --global http.version HTTP/1.1
```

（想撤销：`git config --global --unset http.version`）

同时建议把超时放宽：

```bash
git config --global http.lowSpeedLimit 1000
git config --global http.lowSpeedTime 60
```

## 四、第三招：改用 SSH 通道（通道已实测可达）

SSH 抗重置能力比 HTTPS 强，而且**不用再管 token**。

**4.1 生成密钥**（一路回车，不用设密码）：
```bash
ssh-keygen -t ed25519 -C "你的邮箱"
```

**4.2 复制公钥**：
```bash
cat ~/.ssh/id_ed25519.pub
```
选中输出的整行（以 `ssh-ed25519` 开头），`Ctrl+Insert` 复制。

**4.3 加到 GitHub**：打开 https://github.com/settings/keys → **New SSH key** → Title 随便填（如 `work-pc`）→ Key 粘贴 → **Add SSH key**。

**4.4 切远程地址**：
```bash
git remote set-url origin git@github.com:TIMXU616/autograder.git
```

**4.5 测试**（问 `yes` 就输 yes）：
```bash
ssh -T git@github.com
```
→ 出现 `Hi TIMXU616! You've successfully authenticated...` 即成功。

> 若 22 端口被封，可改用 443 端口：在 `~/.ssh/config` 里加
> ```
> Host github.com
>   Hostname ssh.github.com
>   Port 443
> ```

## 五、第四招：加 Gitee 镜像（国内最稳，全队适用）

手册允许 **GitHub / Gitee 二选一**，两边的仓库都可以作为提交链接。

**5.1** 注册/登录 https://gitee.com → 右上角 `+` → **新建仓库**
- 仓库名称：`autograder`
- 是否开源：**私有**
- ⚠️ 不要勾「使用 Readme 文件初始化」（否则远程非空，推送会报错）

**5.2 加一个第二远程**（保留 GitHub，不动它）：
```bash
git remote add gitee https://gitee.com/你的用户名/autograder.git
```

**5.3 推送**：
```bash
git push -u gitee dev
```

**5.4 以后双推**：
```bash
git push              # 推 GitHub
git push gitee dev    # 推 Gitee（GitHub 挂了就靠它）
```

**5.5 拉人**：Gitee 仓库页 → 管理 → **仓库成员管理** → 邀请 A、C。

## 六、快速判断故障类型

| 报错关键字 | 性质 | 处理 |
|---|---|---|
| `Connection was reset` / `Recv failure` | 网络被掐（间歇） | 重试 / 降级 HTTP1.1 / 换 SSH |
| `Failed to connect ... port 443` | 完全连不上 | 换 SSH 或 Gitee |
| `Authentication failed` / `403` | 凭据问题 | 重新生成 token（勾 `repo`），或改 SSH |
| `Updates were rejected ... fetch first` | 别人先推了 | 先 `git pull --no-rebase --no-edit` 再 push |
| `not a git repository` | 目录不对 | `pwd` 确认在项目根目录 |
| `src refspec ... does not match any` | 分支名打错 | `git branch` 看实际名字 |
| `LF will be replaced by CRLF` | **无害警告** | 忽略即可 |

## 七、铁律

**代码不会因为推送失败而丢失。** 提交（`git commit`）已经写进你硬盘的 `.git` 里了，
网络问题只影响"寄出去"这一步，本地随时可以再推。

只要看到 `git status -sb` 显示 `[ahead N]`，就意味着**东西都在，只差一次成功的 push**。

---

## 八、新故障形态（2026-09-23 实测）：DNS 把 github.com 指到了不通的 IP

### 症状

```
fatal: unable to access 'https://github.com/TIMXU616/autograder.git/':
Failed to connect to github.com port 443 after 21083 ms: Could not connect to server
```

注意和第 6 节表格里的 `Connection was reset` **不是一回事**：
这次是**连都连不上**（超时），不是连上后被掐。

### 实测数据（本机，直连绕过沙箱代理）

| 目标 | 结果 |
|---|---|
| `github.com` → DNS 解析出的 `20.205.243.166` | **不通**（连续 6 次探测全超时，0/6） |
| `github.com` → 手工换成 `140.82.112.3` | **HTTP 401** ✅（401 = 通了，只是要认证） |
| `github.com` → 手工换成 `140.82.121.4` | **HTTP 401** ✅ |
| `github.com` → 手工换成 `140.82.113.3` | 不通 |
| `api.github.com` / `codeload.github.com` | 可达 |
| `raw.githubusercontent.com` / `objects.githubusercontent.com` | 可达 |
| `ssh.github.com:443` / `github.com:22` | 可达 |
| `gitee.com:443` | 可达（HTTP 200） |

**结论：不是 GitHub 挂了，也不是凭据坏了 —— 是本机 DNS 把 `github.com`
解析到了一个当前不通的 IP。GitHub 的其他 IP 完全可用。**

### 修法：改 hosts，把 github.com 钉到可用 IP

**1. 以管理员身份**打开记事本（开始菜单 → 右键「记事本」→ 以管理员身份运行）……

或直接用管理员 PowerShell 一行搞定：

```powershell
Add-Content -Path "$env:windir\System32\drivers\etc\hosts" -Value "140.82.112.3  github.com" -Encoding ASCII
ipconfig /flushdns
```

**2. 验证**（在 Git Bash 里跑，期望输出 `401`）：

```bash
curl --noproxy '*' -o /dev/null -w '%{http_code}\n' \
  "https://github.com/TIMXU616/autograder.git/info/refs?service=git-upload-pack"
```

**3. 推送**：

```bash
cd /d/projects/autograder
git push origin dev
```

> 该 IP 失效时换 `140.82.121.4`（同样实测 401）。GitHub 的边缘 IP 会变，
> 但换了照样能通，改 hosts 前先用上面的 `curl --resolve` 试一下哪个通：
> ```bash
> for ip in 140.82.112.3 140.82.121.4 140.82.113.3; do
>   printf "%-16s " "$ip"
>   curl -s --noproxy '*' --resolve "github.com:443:$ip" -o /dev/null \
>     -w '%{http_code}\n' -m 12 \
>     "https://github.com/TIMXU616/autograder.git/info/refs?service=git-upload-pack"
> done
> ```
>
> 撤销也很简单：把 hosts 里那一行删掉即可。

### 拿不到管理员权限时：走 Gitee 镜像

`gitee.com` 实测通畅（HTTP 200），网页也能打开。按第 5 节建仓库后：

```bash
git remote add gitee https://gitee.com/你的用户名/autograder.git
git push -u gitee dev
```

### 别把「直连」和「走代理」混起来测

本机存在 `HTTP_PROXY` / `HTTPS_PROXY` 环境变量（沙箱代理）。用 `curl` 测 GitHub 时
**必须加 `--noproxy '*'`**，否则请求会走代理、`--resolve` 指定 IP 也不生效，
测出来的 `000` 是代理的失败，不是你网络的真实现象。

