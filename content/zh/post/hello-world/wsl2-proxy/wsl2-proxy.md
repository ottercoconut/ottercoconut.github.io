+++
title = "如何在WSL2上使用本机代理"
date = 2026-01-30T16:31:20+08:00
translationKey = "wsl2-proxy"
tags = ["代理", "网络"]
categories = ["技术", "实用技术"]

[params]
toc = true
+++

由于近日笔者经常用Python下载各种模型，终要解决困扰已久的wsl2与Windows主机代理不互通的问题。笔者浪费了半个下午后终于搞定，在得力助手Gemini的帮助下，主要步骤如下：

1. Windows的`.wslconfig`设置
2. v2rayN的核心设置
3. Windows的防火墙设置
4. wsl2的旧设置清理
5. wsl2的`~/.bashrc`设置
6. wsl2的`curl -v`测试

参考网站：

[Advanced settings configuration in WSL | Microsoft Learn](https://learn.microsoft.com/en-us/windows/wsl/wsl-config)

[WSL2 使用 V2RayN 局域网 proxychains 代理方案 · Issue #2653 · 2dust/v2rayN](https://github.com/2dust/v2rayN/issues/2653)

[记一次用wsl2中共享宿主机的代理-v2rayN - 沉迷于学习，无法自拔^_^](https://hlog.cc/archives/210/)



## .wslconfig

1. 访问Windows下的个人账户文件夹，按下 `Win + R`，输入 `%UserProfile%` 并回车

2. 检查是否有 `.wslconfig` 文件。**如果没有，新建一个文本文件并命名为 `.wslconfig`**

3. 将以下内容粘贴到`.wslconfig`中：

   ```bash
   [wsl2]
   # 开启镜像网络模式
   networkingMode=mirrored
   # 允许 WSL2 访问 Windows 本地服务
   localhostForwarding=true
   # 自动同步代理设置（可选true/false）
   autoProxy=true
   ```

   需注意的是：`autoProxy`这个参数决定了wsl2代理的方式，设置为`true`可以不再配置`~/.bashrc`，但是问题在于：

   1. 当我们使用`env | grep -i proxy`命令，会看到很多奇怪的和网络有关的变量，虽然确实能成功实现代理。
   2. 不能在wsl2中开关代理，导致很多流量都通过代理来走

   后面我们将其设置为`false`，以便于在wsl2内部可以方便地控制代理的开关，保证wsl2系统的清晰透明。

4. 在Windows终端中输入`wsl --shutdown`关闭wsl2

## v2rayN

1. 在v2rayN（撰文时版本为V7.15.7）的基础设置中，启用“**允许来自局域网的连接**”以及“为局域网开启新的端口”（可选）
2. 在v2rayN客户端的主界面左下角能看到**为互联网开放的端口**，笔者这里是`10810`
3. 这里系统代理是“自动配置系统代理”，路由模式是“绕过(Whitelist)”
4. 然后选好节点，保持v2rayN的进行

## FireWall

1. 在 Windows 搜索框输入“防火墙”，选择 **Windows Defender 防火墙**
2. 点击 **“允许应用或功能通过 Windows Defender 防火墙”**。
3. 找到或添加 `v2rayN.exe` 和其核心程序（如 `v2ray.exe` 或 `xray.exe`），确保 **专用** 和 **公用** 都勾选上。通常路径分别在`v2rayN\`和`v2rayN\bin\xray`下
4. 在防火墙高级设置中，新建一个入站规则，允许端口 `10810` 的 TCP 流量（与v2rayN相对应）

## wsl2

### 清理旧设置

```
# 1. 清除旧的、混乱的代理环境变量
unset http_proxy
unset https_proxy
unset no_proxy

# 2. 重新设置正确的代理（指向镜像模式下的本地端口）
export http_proxy="http://127.0.0.1:10810"
export https_proxy="http://127.0.0.1:10810"
```

确保在第一步已开启镜像网络模式并重启好wsl2。当然这步也不是必须的，因为后面`~/.bashrc`会自动处理这些就变量。

### ~/.bashrc

```bash
# 用其它的编辑器同理
sudo vim ~/.bashrc
```

在与Gemini多次实验后，得出以下内容用于添加到`~/.bashrc`底部：

```bash
function proxy_on() {
    # 彻底清理可能残留的变量（防止大小写混用冲突）
    unset http_proxy https_proxy ALL_PROXY NO_PROXY HTTP_PROXY HTTPS_PROXY all_proxy no_proxy
    
    # 设置你验证成功的端口（既然 10810 测通了，就用 10810）
    export hostip="127.0.0.1"
    export port="10810"
    
    export http_proxy="http://$hostip:$port"
    export https_proxy="http://$hostip:$port"
    export all_proxy="socks5://$hostip:$port"
    
    # 这里的 no_proxy 只保留本地回环
    export no_proxy="localhost,127.0.0.1"
    
    echo "WSL Proxy: ON (127.0.0.1:10810)"
}

function proxy_off() {
    unset http_proxy https_proxy ALL_PROXY NO_PROXY HTTP_PROXY HTTPS_PROXY all_proxy no_proxy
    echo "WSL Proxy: OFF"
}
```

保存以上内容后，输入：

~~~bash
source ~/.bashrc
~~~

然后再：

```bash
curl -I https://www.google.com
```

应该就会出现以下内容，表示连接成功：

笔者同时也用`ping`去测试了一下，虽然不成功，但不影响使用。

```bash
HTTP/1.1 200 Connection established
```

笔者再次尝试下载模型，果然成功：

```python
import gensim.downloader as api
wv_from_bin = api.load("glove-wiki-gigaword-200")
```

### 再不成功的解决方案

最有效的方法的就是在完成了上面步骤后，wsl2中输入：

```bash
curl -v https://www.google.com
```

然后把输出的结果交给AI，它会告诉你的。