+++
title = "从零开始配置 VPS"
date = 2026-06-30T15:17:20+08:00
lastmod = 2026-06-30T21:13:11+08:00
translationKey = "vps-config"
tags = ["代理", "网络"]
categories = ["技术", "实用技术"]

[params]
toc = true
+++

近日，笔者对高质量 LLM 的需求，带来了对高峰期仍能保持稳定的代理、纯净度较高的 IP 地址的需要。所以笔者决定不再用机场服务作主力，转向租用海外 VPS 做个人自用代理。

折腾的两个月以来，笔者遇到了 VPS 被恶意攻击、IP 地址被封禁等问题。与此同时，网络上，比如 YouTube 的视频教程大多都极简，只能保证用户成功搭建起入站、客户端，但是既缺少对 VPS 本身安全性的保护教程，也容易使用户“知其然而不知其所以然”。当然也不乏新协议、技术相关的内容，比如使用 XHTTP 协议使被封 IP 的 VPS 重焕生机、BBRv3 的介绍等……这些都是笔者所欠缺的知识。

综上，笔者将从自身的折腾经验出发，分享如何从零开始配置 VPS，主要内容如下：

1. VPS 选购
2. 安全性配置
3. 3x-ui 安装
4. 入站与客户端配置
5. 订阅配置
6. Cloudflare Tunnel

此外，笔者撰写本博客时，3x-ui 的版本是 v3.4.1，后续可能会更新。

参考网站：

- [NodeSeek 论坛](https://www.nodeseek.com)
- [MHSanaei/3x-ui](https://github.com/MHSanaei/3x-ui)

## VPS 选购

这篇博客并非广告，VPS 提供商的来源为 NodeSeek 以及 LLM 的输出（多为 ChatGPT）。笔者在选购的时候，主要是找带有三网优化（TRI）的 VPS 服务，比如 BandwagonHost、DMIT、GigsGigsCloud、Vmiss 和 Hostdare 等一系列 VPS 提供商，它们的价格、地区均有差异。作为中国用户，首先要关注的就是 VPS 的线路，大致有以下几种：

- TRI 在 VPS 商家语境里通常是 Tri-network optimized 的缩写，即“三网优化”。它不是某个运营商的正式线路名称，而是套餐命名方式。一般表示电信、联通、移动三家分别尽量走较优路径，例如电信走 CN2 GIA，联通走 9929 或 4837 优化，移动走 CMI/CMIN2。
- CN2 常见于中国电信方向，全称通常理解为 China Telecom Next Generation Carrier Network，常见分类有 CN2 GT 和 CN2 GIA。GIA，即 Global Internet Access，通常比 GT 更高端，价格更贵，低峰和晚高峰的稳定性也通常更好。
- 9929 通常指中国联通 AS9929，也常被称为联通精品网、CUII，是一类走联通优质国际链路的线路标识。相比联通普通骨干网 AS4837，9929 一般更适合对联通用户优化，常见于香港、日本、美国西海岸等面向中国大陆优化的 VPS。
- 4837 通常指中国联通普通骨干网 AS4837，也就是 China169 Backbone。它覆盖面广、成本相对低，但国际方向在高峰期更容易受到拥塞影响。
- CMI 通常指中国移动国际线路，常见 AS 号是 AS58453；CMIN2 则是近年 VPS 圈里常见的移动高端线路说法，常与 AS58807 相关。对于中国移动用户，CMI/CMIN2 的体验往往比绕路国际 BGP 更稳定。

不同 VPS 的服务详情，节点速率、延迟等数据，均可以通过搜索引擎查阅到，笔者不多赘述。
此外，两个月前笔者挑选 VPS 时，就有优质线路服务短缺的问题，比如 DMIT，笔者观察了许久，时至今日多数产品也都是 "Out of stock" 的状态，其他提供商也是同理（除了配置比较豪华的服务）。现在看来当时能搞到一台 VPS 用到现在，大概是运气好吧。

成功付款后，通常会被分配到一台 VPS 供我们折腾。操作系统的选择个人认为区别不大，管理界面大致如下：

![](/uploads/posts/vps-config/Screenshot_2026-06-30_at_16.07.08.png)

通常这里会有最为重要的 VPS IP 信息，以及一些基本的管理功能。

## 安全性配置

开机后，第一步就是基本的安全性配置，避免被恶意攻击。
笔者在前几天遭遇了一次，原因是因为偷懒没有禁用密码登录，`fail2ban` 的规则也没设置好，于是在被攻击了长达 1 个小时后，IP 也被封了（可能是巧合）。这还是在 IP 被封以后，观察到 CPU 利用率一段时间内竟然持续 100%，才发现的。

首先，通过 SSH 和提供商给出的初始 root 账户连接到 VPS 上（使用提供商的 VNC console 也可以），执行下面的命令进行软件的更新，以及必要的 `ufw` 和 `fail2ban` 的安装：

```bash
apt update && apt full-upgrade -y
apt install -y sudo curl wget vim git ufw fail2ban
```

### SSH 登录

出于历史教训，应尽早关闭密码登录，仅保留 SSH 密钥登录方式。笔者使用了 VPS 官方控制台提供的 OpenSSH 配置功能，它会自动生成好密钥文件到 VPS 中，并关闭密码登录，我需要做的只是把密钥文件配置到客户端的机器上，以便于访问。

切换到客户端机器的用户目录下，找到（或者创建）`.ssh` 目录，存放生成的密钥文件，文件名随意。
之后再创建（或编辑）一个名为 `config` 的文件，需要新增内容样式如下：

```text
Host vps                            # 本地别名（以后 ssh vps）
    HostName 1.2.3.4                # VPS 的 IP 或域名
    User root                       # 登录用户名
    IdentityFile ~/.ssh/id_ed25519  # 私钥路径
    IdentitiesOnly yes              # 强制只用该密钥，避免 SSH 自动尝试其他 key
```

如果要自己生成密钥文件的话，那么流程略有不同，且 VPS 上也要进行对应操作。首先，在客户端机器上生成一个随机密钥：

```bash
ssh-keygen -t ed25519
```

把公钥复制到 VPS 上：

```bash
mkdir -p ~/.ssh
nano ~/.ssh/authorized_keys # 把生成好的密钥复制进去
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

禁用密码登录：

```bash
nano /etc/ssh/sshd_config
```

找到以下字段并修改为：

```bash
PermitRootLogin prohibit-password
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
```

最后重启一下服务：

```bash
systemctl reload ssh
```

### 改 SSH 默认端口

```bash
nano /etc/ssh/sshd_config
```

在其中找到 `Port` 字段，默认值通常是 22，我们把它改成非默认值。
改好后，在客户端机器的 `~/.ssh/` 下也进行修改（或添加）`Port` 字段为相应的值。

### ufw 配置

一开始的时候，我们安装过了 `ufw`，所以先检查一下其状态：

```bash
ufw status
```

输出应该是 `inactive`，不过这不影响我们继续配置。首先，设置其默认策略：

```bash
ufw default deny incoming  # 拒绝所有入站连接（安全默认）
ufw default allow outgoing # 允许所有出站连接（系统正常联网）
```

接下来，要放行 SSH 连接的端口和 Web 入站的端口：

```bash
ufw allow 22/tcp # 默认值是 22，但应该填我们之前修改好的值
ufw allow 443/tcp
ufw allow 443/udp # 如果可能用到 Hysteria2 协议
```

最后，开启 `ufw`，并检查记录是否正确：

```bash
ufw enable
ufw status verbose
```

### fail2ban 配置

在完成 SSH 和防火墙基础加固之后，下一步是启用 `fail2ban` 来防止暴力破解 SSH 登录。

首先确认 `fail2ban` 是否已经安装并运行：

```bash
systemctl status fail2ban
```

检查完成后，启用并启动服务：

```bash
systemctl enable fail2ban
systemctl start fail2ban
```

接下来配置 SSH 防护规则。建议不要直接修改默认配置文件，而是在 `jail.d` 目录下新增配置：

```bash
nano /etc/fail2ban/jail.d/sshd.local
```

写入以下内容：

```text
[sshd]
enabled = true
backend = systemd
port = ssh
maxretry = 3   # 最多尝试三次
findtime = 10m # 10 分钟之内
bantime = 12h  # 封禁时间
```

如果你修改过 SSH 端口，需要同步更新 `port` 字段，例如：`port = 2222`

配置完成后，重启 fail2ban 使其生效：

```bash
systemctl restart fail2ban
```

然后检查 SSH jail 是否正常运行：

```bash
fail2ban-client status
fail2ban-client status sshd
```

最后确认日志中已经开始记录失败登录尝试即可，说明防护已经生效。

### 自动安全更新

用于自动安装系统安全更新，减少 VPS 暴露时间窗口。

```bash
apt install -y unattended-upgrades apt-listchanges
dpkg-reconfigure --priority=low unattended-upgrades
```

检查是否启用：

```bash
cat /etc/apt/apt.conf.d/20auto-upgrades
```

测试运行：

```bash
unattended-upgrade --dry-run --debug
```

## 3x-ui 安装

使用官方脚本安装 3x-ui 面板：

```bash
bash <(curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh)
```

安装器会生成随机用户名、密码和 Web Base Path，端口可以手动指定，也可以随机生成。这些信息在第一次登录前一定要保留好，因为登录到面板上之后，这些都可以修改。格式大致如下：

```text
Username:
Password:
Port:
WebBasePath:
Access URL:
```

之后，脚本会询问证书方式：

```text
1. Let's Encrypt for Domain
2. Let's Encrypt for IP Address
3. Custom SSL Certificate
4. Skip SSL
```

多数教程在这里会让用户选择 1，去分配一个域名给 3x-ui 面板，便于在公网直接通过这个域名访问，笔者第一次安装时也是这样做的。

但是现在我认为没有必要，或者说暴露到公网上有一定风险，所以选择了 "4. Skip SSL"，后续通过 SSH Tunnel 来访问面板。

之后脚本会询问是否绑定到 127.0.0.1，输入：y (yes)

后续检查：

```bash
ss -lntp | grep x-ui
```

如果上一步选择了 "4. Skip SSL"，输出结果应该是：

```bash
127.0.0.1:面板端口
```

或者是：

```bash
0.0.0.0:面板端口
```

安装成功之后，检查运行状态：

```bash
systemctl status x-ui --no-pager
systemctl is-enabled x-ui
```

### SSH Tunnel 访问面板

在客户端机器运行：

```bash
ssh -i ~/.ssh/你的私钥 \
  -p 你的 SSH 端口 \
  -N \
  -L 2222:127.0.0.1:面板端口 \
  root@你的 VPS 公网 IP
```

或者修改 `~/.ssh/config`，实现 SSH 连接和隧道建立的一举两得：

```text
Host vps
    HostName 1.2.3.4
    User root
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
    LocalForward 面板端口号 127.0.0.1:面板端口号 # 新增字段用于建立隧道
```

## 入站与客户端配置

![](/uploads/posts/vps-config/Screenshot_2026-06-30_at_19.52.05.png)

### 用户配置

登录后，我建议先在左侧栏的 “面板设置” -> “安全设定” -> “管理员凭据” 中，把用户名和密码进行更换。

### 入站配置

之后，找到 “入站” -> “新建入站”，这是搭建代理服务的第一步：

1. 我们先建立一个 VLESS + TCP + REALITY 的入站，“基础配置” 页中，“备注”随意（最好不留空），“协议”选择 “vless”。
   如果之前安装面板时，给它分配了域名，那么“分享地址策略”不用更改；如果没有，那么“分享地址策略”要改为“自定义”，并在“自定义分享地址”中填写 VPS 的 IP。
   “端口”改为 443。
2. “传输” 页，“传输”项保持默认的 “RAW” 不变即可（即 TCP）。
3. “安全” 页，“安全”项选择 “REALITY”。
   “目标”栏，可以像多数教程那样，填一个大型网站的域名，比如 "www.microsoft.com:443"，同时“SNI”栏和“目标”保持一致，填 "www.microsoft.com"。
   或者说去筛选一下域名，而不是随便填，原因如下：
   - REALITY 的目标域名不是随便拿来“装样子”的，它参与服务端对外握手特征的构造，也要求你的 VPS 到这个目标站能正常建立 TLS 1.3 / h2 连接。
   - 所以不能无脑填大网站：大网站往往有复杂 CDN、区域策略、TLS 策略差异。某个域名在你本地能访问，不代表从 VPS 所在机房访问也正常。
   - 更合理的做法是结合 VPS 的物理位置和网络出口，选一个从 VPS 访问稳定、延迟较低、支持 TLS 1.3 和 h2、不会跳转异常的目标站。简单说：REALITY 目标域名要按“VPS 视角”测试，而不是按“用户浏览器视角”随便填。比如 VPS 的物理位置在日本，那么这里填微软的域名，显得非常假，因为访问微软不需要用户访问一个日本的 IP，中国也有微软的服务器。
4. 最后下滑，选择 “创建”，第一个入站就创建好了。

### 客户端配置

接着，我们还需要创建 “客户端”，虽然 VPS 的用途一般是个人自用，但是不同的设备也可以安排不同的客户端，便于管理。找到 “客户端” -> “添加客户端”：

1. “基本” 页，只需在 “关联入站” 项，选择对应的“入站”即可，其他的配置项按需更改。
2. “凭据” 页，只需在 "Flow" 项，选择 "xtls-rprx-vision" 即可，其他的配置项无需修改。
3. 选择 “创建”，客户端就配置完毕了。

理论上来讲，如果安装面板时分配了域名，那么现在只要点击 “客户端信息”，复制订阅链接到客户端，就算成功了。
但是订阅设置还有几项有待调整。

## 订阅配置

### 路径配置

“面板设置” -> “订阅设置” -> “常规”，找到 “URL 路径” 项进行修改（这也是面板建议我们修改的，从而保证安全性），笔者是生成了一个 “CSPRNG 随机数”，改掉了原本的 “/sub/”，但具体改成什么都可以，只要能保证其安全。

### Clash 配置

由于笔者用的客户端都是 Clash 系的，所以在此提及一下。

1. 确认 “面板设置” -> “订阅设置” -> “常规” 中的 “Clash / Mihomo 订阅” 是开启状态。
2. “面板设置” -> "Sub Formats" -> “常规”，找到 “Clash URL 路径” 进行修改，和上面路径配置同理。
3. “面板设置” -> “订阅设置” -> "Clash / Mihomo"，开启 “启用路由” 项，然后填写下面的 “全局路由规则”。

路由规则的作用是分流：需要代理的服务走 VPS，例如 OpenAI、GitHub、Google；本来就能直连且更快的流量直接走本地网络。这样延迟更低、VPS 流量消耗更少，也更不容易触发网站风控。国内网站、本地局域网、银行/政务/支付、部分游戏和 CDN，如果都走 VPS，可能变慢、风控、定位异常，甚至访问失败。像 NAS、路由器、打印机这类内网地址更不应该走代理。

具体 “全局路由规则” 该填什么，笔者给出 ChatGPT 生成的模板：

```yaml
# 1. 私网 / 广告
GEOSITE,private,DIRECT
GEOIP,private,DIRECT,no-resolve
GEOSITE,category-ads-all,REJECT

# 2. AI / Agent 显式代理
GEOSITE,openai,PROXY
DOMAIN-SUFFIX,openai.com,PROXY
DOMAIN-SUFFIX,chatgpt.com,PROXY
DOMAIN-SUFFIX,oaistatic.com,PROXY
DOMAIN-SUFFIX,oaiusercontent.com,PROXY
DOMAIN-SUFFIX,anthropic.com,PROXY
DOMAIN-SUFFIX,claude.ai,PROXY
DOMAIN-SUFFIX,githubcopilot.com,PROXY
DOMAIN-SUFFIX,copilot.microsoft.com,PROXY

# 3. 常用代理
GEOSITE,google,PROXY
GEOSITE,github,PROXY
GEOSITE,youtube,PROXY
GEOSITE,telegram,PROXY
GEOIP,telegram,PROXY,no-resolve
GEOSITE,twitter,PROXY
GEOSITE,gfw,PROXY
GEOSITE,geolocation-!cn,PROXY

# 4. 国内直连
GEOSITE,apple-cn,DIRECT
GEOSITE,microsoft@cn,DIRECT
GEOSITE,steam@cn,DIRECT
GEOSITE,category-games@cn,DIRECT
GEOSITE,cn,DIRECT
GEOIP,CN,DIRECT,no-resolve
```

## Cloudflare Tunnel

如果和笔者一样，没有给面板配置域名的话，经过了上述一系列操作，订阅现在仍然无法从公网获取。接下来，我们为订阅服务创建 Cloudflare Tunnel，保证订阅正常的获取和更新。当然，面板还是不会暴露给公网的，代理入站还是走 VPS IP 443 端口。

首先，更改 “面板设置” -> “订阅设置” -> “常规” 下的 “监听端口”，默认是 2096。

安装 Cloudflare 服务：

```bash
apt install -y cloudflared  # 安装 cloudflared
cloudflared tunnel login    # 登录 Cloudflare
```

这里会输出一个链接，我们复制到浏览器，完成 Cloudflare 的登录。

接着，创建隧道，这里仍然需要用到域名：

```bash
cloudflared tunnel create xui-sub                       # xui-sub 是示例隧道名
cloudflared tunnel route dns xui-sub your.domain.com    # 给域名创建 DNS 路由
```

然后写 `/etc/cloudflared/config.yml`：

```yaml
tunnel: 你的-tunnel-id
credentials-file: /etc/cloudflared/你的-tunnel-id.json

ingress:
  - hostname: docs.tolink.info
    path: /clash/.*
    service: http://127.0.0.1:2096

  - hostname: docs.tolink.info
    service: http_status:404

  - service: http_status:404
```

这里最关键的是：第一条只匹配 `/clash/.*`，其他路径全部 404。Cloudflare Tunnel 的 `ingress` 规则按顺序匹配；
没有 `path` 的 `hostname` 规则会匹配该域名下所有路径，所以 404 兜底必须放在订阅规则后面。
Cloudflare 官方文档也说明 `ingress rules` 会按顺序匹配，并要求最后配置兜底规则。

验证配置：

```bash
cloudflared --config /etc/cloudflared/config.yml tunnel ingress validate
cloudflared --config /etc/cloudflared/config.yml tunnel ingress rule https://your.domain.com/clash/your_clash_baseurl
cloudflared --config /etc/cloudflared/config.yml tunnel ingress rule https://your.domain.com/anything
```

期望输出：

```bash
/clash/test  → http://127.0.0.1:2096    # 默认端口是 2096
/anything    → http_status:404
```

最后安装为服务并启动：

```bash
cloudflared --config /etc/cloudflared/config.yml service install
systemctl enable --now cloudflared
systemctl status cloudflared --no-pager
```

如果还想更加安全，限制对订阅前缀的高频扫描，那么需要在 Cloudflare 的 "Security" -> "Security Rules" -> "Rate limiting rules" 中填写相应的规则，比如：

```text
(http.host eq "docs.tolink.info" and starts_with(http.request.uri.path, "/clash/"))
```

## 结语

至此，一台 VPS 从选购、安全加固、代理入站、客户端订阅到 Cloudflare Tunnel 的基本配置就完成了。相比直接套用一键脚本，这套流程确实麻烦一些，但好处是每一步都更可控：知道哪些端口暴露在公网、面板如何访问、订阅如何分发，也知道出现问题时该从哪里排查。

当然，网络环境和服务端工具都在持续变化，这篇文章更像是一份当前可用的配置记录，而不是一劳永逸的标准答案。后续如果遇到新的封锁、协议变化或更稳妥的实践，笔者也会继续更新。
