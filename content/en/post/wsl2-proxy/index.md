+++
title = "How to Use Host Proxy on WSL2"
date = 2026-01-30T16:31:20+08:00
translationKey = "wsl2-proxy"
tags = ["Proxy", "Networking"]
categories = ["Tech", "Practical Tech"]

[params]
toc = true
+++

Since I've been frequently downloading various models with Python recently, I finally decided to solve the long-standing issue of WSL2 not being able to use the Windows host's proxy. After wasting half an afternoon, I finally got it working. With the help of my capable assistant Gemini, the main steps are as follows:

1. `.wslconfig` settings in Windows
2. Core settings of v2rayN
3. Firewall settings in Windows
4. Cleaning up old settings in WSL2
5. `~/.bashrc` settings in WSL2
6. `curl -v` testing in WSL2

References:

[Advanced settings configuration in WSL | Microsoft Learn](https://learn.microsoft.com/en-us/windows/wsl/wsl-config)

[WSL2 使用 V2RayN 局域网 proxychains 代理方案 · Issue #2653 · 2dust/v2rayN](https://github.com/2dust/v2rayN/issues/2653)

[记一次用wsl2中共享宿主机的代理-v2rayN - 沉迷于学习，无法自拔^_^](https://hlog.cc/archives/210/)



## .wslconfig

1. Access your personal account folder in Windows. Press `Win + R`, enter `%UserProfile%`, and hit Enter.

2. Check if there is a `.wslconfig` file. **If not, create a new text file and name it `.wslconfig`.**

3. Paste the following content into `.wslconfig`:

   ```bash
   [wsl2]
   # Enable mirrored networking mode
   networkingMode=mirrored
   # Allow WSL2 to access Windows localhost
   localhostForwarding=true
   # Automatically synchronize proxy settings (optional: true/false)
   autoProxy=true
   ```

   Note that the `autoProxy` parameter determines how WSL2 handles the proxy. Setting it to `true` means you don't need to configure `~/.bashrc` anymore, but the problems are:

   1. When we use the `env | grep -i proxy` command, we will see many strange network-related variables, even though the proxy does successfully work.
   2. The proxy cannot be toggled on or off within WSL2, causing a lot of traffic to go through the proxy unnecessarily.

   Later, we will set it to `false` so that we can easily control the proxy switch inside WSL2, ensuring a clear and transparent WSL2 system.

4. In the Windows terminal, enter `wsl --shutdown` to shut down WSL2.

## v2rayN

1. In the basic settings of v2rayN (version V7.15.7 at the time of writing), enable "**Allow connections from the LAN**" and "Open a new port for the LAN" (optional).
2. At the bottom left of the v2rayN client's main interface, you can see the **port open for the internet**, which is `10810` in my case.
3. The system proxy here is "Set system proxy automatically", and the routing mode is "Bypass (Whitelist)".
4. Then select a node and keep v2rayN running.

## FireWall

1. Type "firewall" in the Windows search box and select **Windows Defender Firewall**.
2. Click **"Allow an app or feature through Windows Defender Firewall"**.
3. Find or add `v2rayN.exe` and its core programs (such as `v2ray.exe` or `xray.exe`), ensuring that both **Private** and **Public** are checked. The usual paths are under `v2rayN\` and `v2rayN\bin\xray`, respectively.
4. In the advanced settings of the firewall, create a new inbound rule to allow TCP traffic on port `10810` (corresponding to v2rayN).

## wsl2

### Cleaning Up Old Settings

```
# 1. Clear old, messy proxy environment variables
unset http_proxy
unset https_proxy
unset no_proxy

# 2. Re-set correct proxy (pointing to localhost port in mirrored mode)
export http_proxy="http://127.0.0.1:10810"
export https_proxy="http://127.0.0.1:10810"
```

Ensure that you have enabled mirrored networking mode in the first step and successfully restarted WSL2. Of course, this step is not strictly necessary either, because `~/.bashrc` will automatically handle these old variables later.

### ~/.bashrc

```bash
# Same applies to other editors
sudo vim ~/.bashrc
```

After multiple experiments with Gemini, here is the content to append to the bottom of `~/.bashrc`:

```bash
function proxy_on() {
    # Thoroughly clean up any residual variables (prevent conflicts from mixed case)
    unset http_proxy https_proxy ALL_PROXY NO_PROXY HTTP_PROXY HTTPS_PROXY all_proxy no_proxy
    
    # Set the port you verified works (since 10810 was tested successfully, use 10810)
    export hostip="127.0.0.1"
    export port="10810"
    
    export http_proxy="http://$hostip:$port"
    export https_proxy="http://$hostip:$port"
    export all_proxy="socks5://$hostip:$port"
    
    # no_proxy here only keeps localhost
    export no_proxy="localhost,127.0.0.1"
    
    echo "WSL Proxy: ON (127.0.0.1:10810)"
}

function proxy_off() {
    unset http_proxy https_proxy ALL_PROXY NO_PROXY HTTP_PROXY HTTPS_PROXY all_proxy no_proxy
    echo "WSL Proxy: OFF"
}
```

After saving the above content, enter:

~~~bash
source ~/.bashrc
~~~

And then:

```bash
curl -I https://www.google.com
```

The following output should appear, indicating a successful connection:

I also tested it with `ping`, which didn't work but doesn't affect its usability.

```bash
HTTP/1.1 200 Connection established
```

I tried downloading the model again, and it successfully worked:

```python
import gensim.downloader as api
wv_from_bin = api.load("glove-wiki-gigaword-200")
```

### Solution If It Still Fails

The most effective method is, after completing the above steps, to enter the following in WSL2:

```bash
curl -v https://www.google.com
```

Then feed the output result to an AI, and it will tell you what to do.
