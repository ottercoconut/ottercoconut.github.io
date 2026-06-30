+++
title = "从零开始配置VPS"
date = 2026-06-30T15:17:20+08:00
translationKey = "vps-config"
tags = ["代理", "网络"]
categories = ["技术", "实用技术"]

[params]
toc = true
+++

近日，出于笔者对高质量LLM的需求，引发了对高峰期仍能保持稳定的代理、纯净度较高的IP地址的需要。所以笔者决定不再用机场服务作主力，转向租用海外VPS做个人自用代理。

折腾的两个月以来，笔者遇到了VPS被恶意攻击、IP地址被封禁等问题。与此同时，网络上，比如YouTube的视频教程大多都极简，只能保证用户成功搭建起入站、客户端，但是既缺少对VPS本身安全性的保护教程，也容易使用户“知其然而不知其所以然”。但也不乏新协议、技术相关的内容，比如使用XHTTP协议使被封IP的VPS重焕生机、BBRv3的介绍等...这些是笔者所欠缺的知识。

综上，笔者将从自身的折腾经验出发，分享如何从零开始配置VPS，主要内容如下：

1. VPS 选购
2. 安全性配置
3. 3x-ui 安装
4. 入站与客户端配置
5. clash 订阅配置
6. CloudFlare Tunnel
7. 客户端导入订阅

参考网站：

- [NodeSeek 论坛](https://www.nodeseek.com)
- [MHSanaei/3x-ui](https://github.com/MHSanaei/3x-ui)

## VPS选购

这篇博客并非广告，VPS 提供商的来源为 NodeSeek 以及 LLM 的输出（多为ChatGPT）。笔者在选购的时候，主要是找带有三网优化（TRI）的 VPS 服务，比如BandwagonHost、DMIT、GigsGigsCloud、Vmiss和Hostdare等一系列 VPS 提供商，它们的价格、地区均有差异。作为中国用户，首先要关注的就是 VPS 的线路，大致有以下几种：

- TRI 在 VPS 商家语境里通常是 Tri-network optimized 的缩写，即“三网优化”。它不是某个运营商的正式线路名称，而是套餐命名方式。一般表示电信、联通、移动三家分别尽量走较优路径，例如电信走 CN2 GIA，联通走 9929 或 4837 优化，移动走 CMI/CMIN2。
- CN2 常见于中国电信方向，全称通常理解为 China Telecom Next Generation Carrier Network，常见分类有 CN2 GT 和 CN2 GIA。GIA，即 Global Internet Access，通常比 GT 更高端，价格更贵，低峰和晚高峰的稳定性也通常更好。
- 9929 通常指中国联通 AS9929，也常被称为联通精品网、CUII，是一类走联通优质国际链路的线路标识。相比联通普通骨干网 AS4837，9929 一般更适合对联通用户优化，常见于香港、日本、美国西海岸等面向中国大陆优化的 VPS。
- 4837 通常指中国联通普通骨干网 AS4837，也就是 China169 Backbone。它覆盖面广、成本相对低，但国际方向在高峰期更容易受到拥塞影响。
- CMI 通常指中国移动国际线路，常见 AS 号是 AS58453；CMIN2 则是近年 VPS 圈里常见的移动高端线路说法，常与 AS58807 相关。对于中国移动用户，CMI/CMIN2 的体验往往比绕路国际 BGP 更稳定。

不同的 VPS 的服务详情，节点速率、延迟等数据，均可以通过搜索引擎查阅到，笔者不多赘述。
此外，两个月前笔者挑选 VPS 时，就有优质线路服务短缺的问题，比如 DMIT，笔者观察了许久，时至今日大多产品也都是"Out of stock"的状态，其它的提供商也是同理（除了配置比较豪华的服务）。现在看来当时能搞到一台 VPS 用到现在，大概是运气好吧。

下面，当成功付款后，会被分配到一台 VPS 供我们折腾，操作系统的选择个人认为区别大不，管理界面大致如下：

![](/uploads/posts/vps-config/Screenshot_2026-06-30_at_16.07.08.png)

通常这里会有最为重要的，VPS 的 IP 信息，以及一些基本的管理功能。

## 安全性配置

开机后，第一步就是基本的安全性配置，避免被恶意攻击。
笔者在前几天遭遇了一次，原因是因为偷懒没有禁用密码登录，fail2ban的规则也没设置好，于是在被攻击了长达1个小时后，IP也被封了（可能是巧合）。这还是 IP 被封了以后，发现 CPU 利用率在一段时间内竟是 100% 发现的。

首先，通过 SSH 和提供的最初的 root 账户连接到 VPS 上（使用提供商的 VNC console 也可以），执行下面的命令进行软件的更新，以及必要的 `ufw` 和 `fail2ban` 的安装：

```bash
apt update && apt full-upgrade -y
apt install -y sudo curl wget vim git ufw fail2ban
```

### SSH登录

出于历史教训，应尽早关闭密码登录，仅保留 SSH 密钥登录方法。笔者是用了 VPS 官方控制台的 openSSH，它会自动生成好密钥文件到 VPS 中，并关闭密码登录，我需要做的只是把密钥文件配置到客户端的机器上，以便于访问。

切换到客户端机器的用户目录下，找到（或者创建）`.ssh` 目录，存放生成的密钥文件，文件名随意。
之后再创建（或编辑）一个名为 `config` 的文件，需要新增内容样式如下：

```plain text
Host vps
    HostName 1.2.3.4
    User root
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
```

字段解释如下：

```plain text
Host            : 本地别名（以后 ssh vps）
HostName        : VPS 的 IP 或域名
User            : 登录用户名（root / deploy）
IdentityFile    : 私钥路径
IdentitiesOnly  : 强制只用该密钥，避免 SSH 自动尝试其他 key
```

如果要自己生成密钥文件的话，那么顺序不同，且 VPS 上也要进行对应操作。首先，在客户端机器上生成一个随机密钥：

```bash
ssh-keygen -t ed25519
```

把密钥复制到 VPS 上：

```bash
mkdir -p ~/.ssh
nano ~/.ssh/authorized_keys # 把生成好的密钥复制进去
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

