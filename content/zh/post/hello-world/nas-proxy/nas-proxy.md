---
title: 群晖NAS代理及Emby配置
date: 2026-02-16 11:12:15
lang: zh-CN
translation_key: nas-proxy
tags: [代理, 网络]
categories: 
	- 技术
	- 实用技术
---

近日笔者在使用群晖NAS的v2rayA时遇到了时间同步不正确导致的无法正常使用的问题，导致emby无法刮削。虽然不知道原因，但也是个老问题了，版本很旧，而且用的是第三方软件市场的docker，现在docker也不能裸连获取了。下面是解决经验：

1. 重新安装v2rayA
2. 配置docker版的emby。

参考网站：

[Linux 后备安装方式 - v2rayA](https://v2raya.org/docs/prologue/installation/linux/)

[XTLS/Xray-core: Xray, Penetrates Everything. Also the best v2ray-core. Where the magic happens. An open platform for various uses.](https://github.com/XTLS/Xray-core)

[群晖实现透明代理 - v2rayA](https://v2raya.org/docs/advanced-application/synology-transparent-proxy/)

[sjtuross/syno-iptables: Some missing iptables modules for Synology](https://github.com/sjtuross/syno-iptables)

[群晖 DSM 7.2 为 Container Manager（docker）设置代理_群晖docker设置代理-CSDN博客](https://blog.csdn.net/caca_66/article/details/150264099)



## v2rayA

由v2rayA的官方文档可见，群晖并没有特别适配的版本，所以采用通用的二进制文件进行安装。既然裸连也无法从github上拉取文件，我们在电脑上下好传到NAS上。此外，下面的安装内容实则和文档略有不同。

1. 拷贝v2rayA和xray

   ```bash
   cp v2raya_linux_x64 /usr/local/bin/v2raya
   cp xray /usr/local/bin/
   chmod +x /usr/local/bin/v2raya
   chmod +x /usr/local/bin/xray
   ```

2. 拷贝xray自带的GFWList代理规则文件：`geoip.dat`和`geosite.dat`

   ~~~bash
   cd /usr/local/share
   mkdir xray
   cp .../g* xray
   ~~~

3. 修改`service`配置文件

   ~~~bash
   sudo vi /etc/systemd/system/v2raya.service
   ~~~

   内容由ChatGPT结合官方文档生成：

   ~~~bash
   [Unit]
   Description=v2rayA Service
   After=network.target
   
   [Service]
   Type=simple
   User=root
   Environment="V2RAYA_CONFIG=/usr/local/etc/v2raya"
   Environment="V2RAYA_LOG_FILE=/tmp/v2raya.log"
   Environment="XRAY_LOCATION_ASSET=/usr/local/share/xray"
   ExecStart=/usr/local/bin/v2raya --passcheckroot
   Restart=on-failure
   LimitNOFILE=1000000
   
   [Install]
   WantedBy=multi-user.target
   
   ~~~

4. 激活v2rayA，根据官方文档，采用服务的形式运行

   ~~~bash
   sudo systemctl start v2raya
   sudo systemctl status v2raya
   ~~~

   配置开机自启。理论上这步之后配置完毕，笔者又顺便解决了群晖用不了透明代理的问题

   ~~~bash
   sudo systemctl enable v2raya
   sudo systemctl is-enabled v2raya
   ~~~

5. 激活透明代理

   | arch       | kernel   | iptables version | system model | platform version |
   | ---------- | -------- | ---------------- | ------------ | ---------------- |
   | apollolake | 4.4.180+ | v1.8.3           | DS918+       | 7.0.1-42218      |
   | apollolake | 4.4.59+  | v1.6.0           | DS918+       | 6.2.3-25426      |
   | broadwell  | 3.10.105 | v1.6.0           | DS3617xs     | 6.2.3-25426      |
   | bromolow   | 3.10.105 | v1.6.0           | DS3615xs     | 6.2.3-25426      |
   | geminilake | 4.4.180+ | v1.8.3           | DS920+       | 7.1-42661        |
   | geminilake | 4.4.302+ | v1.8.3           | DS220+       | 7.2-64570        |

   由于群晖系统的原因，先根据型号确定架构，然后从github仓库中下好的模块中选出适配机器的文件（比如笔者的DS224是geminilake）

   上传相应的ko模块至`/lib/modules/`，上传相应的so模块至`/usr/lib/iptables/`，即可。

   运行`sudo -i`之后再运行以下`insmod`命令尝试加载ko内核模块。由于模块互相有依赖性，需按一定顺序加载

   ~~~bash
   insmod /lib/modules/nfnetlink.ko
   insmod /lib/modules/ip_set.ko
   insmod /lib/modules/ip_set_hash_ip.ko
   insmod /lib/modules/xt_set.ko
   insmod /lib/modules/ip_set_hash_net.ko
   insmod /lib/modules/xt_mark.ko
   insmod /lib/modules/xt_connmark.ko
   insmod /lib/modules/xt_comment.ko
   insmod /lib/modules/xt_TPROXY.ko
   insmod /lib/modules/xt_socket.ko
   insmod /lib/modules/iptable_mangle.ko
   insmod /lib/modules/textsearch.ko
   insmod /lib/modules/ts_bm.ko
   insmod /lib/modules/xt_string.ko
   
   insmod /lib/modules/nf_nat_ipv6.ko
   insmod /lib/modules/nf_nat_masquerade_ipv6.ko
   insmod /lib/modules/ip6t_MASQUERADE.ko
   insmod /lib/modules/ip6table_nat.ko
   insmod /lib/modules/ip6table_raw.ko
   insmod /lib/modules/ip6table_mangle.ko
   ~~~

   但是系统重启后，模块可能需要重新加载。而笔者不再使用透明代理，所以没再研究。

## Emby

在配置好v2rayA后，即使采用了改配置文件的办法，emby的流量仍不能成功地通过v2rayA来走，各种修改配置ip后无果，于是自然想到是docker变成本机服务导致的。

在v2rayA上多次修改配置后，终于发现开启透明代理解决问题，同时也解决了连接不上Docker仓库的问题，但更大的问题是启用透明代理会使外网访问全部失败（亏好内网还能连接）。“透明代理”我想可以理解为“全局代理”。

Docker(Container Manager)单独设置代理的问题详见前言链接。

1. 在“映像”中选中emby并运行，在“存储空间设置”中加入媒体库的路径，在“环境”中加入三个环境变量，“网络”中选择`host`模式：

   ~~~bash
   HTTP_PROXY = http://127.0.0.1:20171
   HTTPS_PROXY = http://127.0.0.1:20171
   NO_PROXY = localhost,127.0.0.1
   ~~~

2. 完成基本设置，安装好之前的动漫相关的插件，刮削成功。

