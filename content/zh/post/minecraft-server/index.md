+++
title = "在Linux(CentOS)系统上部署Minecraft服务器"
date = 2025-03-19T18:48:59+08:00
translationKey = "minecraft-server"
tags = ["服务器", "Linux", "Minecraft"]
categories = ["技术", "实用技术"]

[params]
toc = true
+++

笔者近日配置好了物理服务器，便想利用起来建一个我的世界服务器，经熬夜研究后成功，将本攻略分享出来，希望能帮到大家，尤其是没有公网环境的Linux用户(像我一样)



### 参考网站

[在 RHEL 上安装并使用红帽构建的 OpenJDK 21 | Red Hat Product Documentation](https://docs.redhat.com/zh-cn/documentation/red_hat_build_of_openjdk/21/html-single/installing_and_using_red_hat_build_of_openjdk_21_on_rhel/index#installing-jre-on-rhel-using-yum_openjdk)

[SakuraFrp 启动器安装 / 使用指南 | SakuraFrp 帮助文档](https://doc.natfrp.com/launcher/usage.html)

[CentOS | Docker Docs](https://docs.docker.com/engine/install/centos/)

[Linux终端开服教程★无面板★Minecraft_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1iv4y1P7wJ/?spm_id_from=333.1007.top_right_bar_window_history.content.click&vd_source=c8beb52bf015e61e5378008c684545a4)

- 来自B站的UP主``翱翔大使``，是全篇的主要思路来源  

  

## Java配置

运行我的世界需要，须对应版本的Java环境，笔者这里安装的是OpenJDK21

```bash
sudo yum install java-21-openjdk
java -version //验证是否成功安装
```

如果服务器有多个Java版本，可以用``alternatives``进行版本切换

```bash
alternatives --config java
```

如图，我们输入``2``并回车，就切换到了需要的版本

![Screenshot_2025-03-19_191616.png](/img/Minecraft-server/Screenshot_2025-03-19_191616.png)


## 游戏部署

首先在下面这个网址下载Minecraft的服务器端，这里我下的是支持Fabric的Banner(1.20.1)

[MohistMC]([MohistMC - 主页](https://www.mohistmc.com/))

![](/uploads/posts/Minecraft-server/Screenshot_2025-03-19_185204.png)

![](/uploads/posts/Minecraft-server/Screenshot_2025-03-19_185231.png)

下载完成后是个类似``banner-1.20.1-800-server.jar``的文件，接下来打开SSH软件，在服务器上操作：

```bash
cd /home/username //切换到个人文件夹或者想安装的位置
mkdir Minecraft //创建存放游戏的文件夹
cd Minecraft
```

我们用SSH软件中的SFTP功能(或其他文件传输功能)，将刚才的游戏文件``banner-1.20.1-800-server.jar``拷贝到新建的文件夹``/home/username/Mineraft``中  



接着我们来写一个服务器的启动脚本

```bash
nano start.sh
```

其中内容如下填写，但注意各参数的作用

- ``-Xmx``是最大分配内存，``-Xms``是最小分配内存，笔者有32GB内存，为游戏分配了6G(其实可以多分点)
- ``banner-1.20.1-800-server.jar``是刚才下载的游戏文件名

```bash
java -Xmx6144M -Xms6144m -jar banner-1.20.1-800-server.jar
stty echo
```

按``Ctrl + O``写入，``Enter``确认写入，``Ctrl + X``退出

接着为``start.sh``赋权，避免无权限访问的情况

```bash
chmod 777 start.sh
```



然后安装``screen``，简单来说，``screen``是帮用户创建独立会话，并可以随时恢复的工具

```bash
yum install screen
```

  ``screen``有如下几个常用命令

```bash
screen -S [name] //新建名为"name"的screen
screen -ls //列出所有运行中的screen的名称和端口
screen -r [port] //返回端口号为port的screen
```



接着，新建一个``screen``运行脚本

```bash
screen -S Minecraft
```

在新出现的会话中，运行``start.sh``

```bash
./start.sh
```

然后一路顺畅，笔者在这里没有遇到报错，最后来到``...EULA...``让我们同意EULA协议，输入``true``后回车，等待一下，游戏服务器就在``25565``端口上成功运行了

若想离开Minecraft的这个``screen``按下``Ctrl+A+D``即可

关于游戏规则的更改(比如”是否允许非正版玩家加入“)，需要修改``server.properties``的内容  



---



关于连接，如果是云服务器，在管理界面映射一下端口，然后在客户端的Minecraft中连接``域名:端口``即可

但是像笔者这样的物理服务器，或者说安装了Linux的设备，个人PC，在没有公网IP的情况下，就要继续内网穿透了  



## 内网穿透

笔者在这里使用我的世界领域中比较有名且良心的``SakuraFrp``进行内网穿透，其它工具也大同小异

### Docker



Linux上的``SakuraFrp``是基于Docker运行的，所以下面我们先部署Docker，操作完全根据官方文档进行

```bash
sudo dnf -y install dnf-plugins-core
sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
```

笔者在下面这遇到了安装速度十分缓慢，和下载失败的问题，重新执行命令再执行一次便解决了

```bash
sudo dnf install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

安装完毕后

```bash
sudo systemctl enable --now docker
```

```bash
sudo docker run hello-world
```

  

上面的这个``run hello-world``测试极有可能失败，下面来解决这个问题，参考了下面两篇文章：

[【完全解决】Docker安装完成运行hello-world镜像失败：Unable to find image ‘hello-world:latest‘ locallylatest:_unable to find image 'hello-world:latest' locally-CSDN博客](https://blog.csdn.net/Fengdf666/article/details/140236208)

[Docker运行hello-world镜像失败或超时 - Paul7777 - 博客园](https://www.cnblogs.com/paul-liang/p/18384633)  



综合上面二者，最终是能解决问题的，先来配置``daemon``文件

```bash
nano /etc/docker/daemon.json
```

复制下面的内容进去

- 在笔者测试的时间(2025/3/19)下面的镜像源还是可用的

  

```json
{
  "registry-mirrors": [
        "https://h59pkpv6.mirror.aliyuncs.com",
        "https://registry.docker-cn.com",
        "https://docker.mirrors.ustc.edu.cn",
        "https://hub-mirror.c.163.com",
        "https://mirror.baidubce.com",
        "https://do.nark.eu.org",
        "https://dc.j8.work",
        "https://docker.m.daocloud.io",
        "https://dockerproxy.com",
        "https://docker.nju.edu.cn"
]
}
```

保存 + 退出，接下来重启docker，再执行一次测试

```bash
sudo systemctl daemon-reload
sudo systemctl restart docker
docker run hello-world
```

笔者到这就已经成功安装好docker了，若是测试仍不通过，请检查``daemon.json``的内容，是否少了或者多了逗号和括号

  

### SakuraFrp

``SakuraFrp``在Linux上的部署，官方文档给出了详细的方案

![](/uploads/posts/Minecraft-server/Screenshot_2025-03-19_203047.png)

首先在终端以管理员身份运行

```bash
sudo bash -c ". <(curl -sSL https://doc.natfrp.com/launcher.sh)"
```

安装好后，应该是会自动输出日志，并需要填写访问密钥，这个(或者说接下来的操作)可以在``SakuraFrp``官网的管理面板找到

![](/uploads/posts/Minecraft-server/Screenshot_2025-03-19_203530.png)

登录好之后就能看到其日志文件，下面是常规的启动并查看日志的操作

```bash
docker start natfrp-service
docker logs natfrp-service
```

  

如图，接下来需要用物理方式操作下服务器

![](/uploads/posts/Minecraft-server/Image_146159838978722.png)

打开浏览器(一般Linux自带Firefox)访问“使用”后面的网址打开``WebUI``

然后看到“隧道”那什么都没有，只有一个加号，这时我们在打开``SakuraFrp``的管理面板，找到服务下的``隧道列表``，新建两个隧道，如图所示：

![](/uploads/posts/Minecraft-server/Screenshot_2025-03-19_204855.png)

![](/uploads/posts/Minecraft-server/Screenshot_2025-03-19_205010.png)

第一个端口号为7102的是服务器上``SakuraFrp``的``WebUI``，以便远程管理

第二个端口号为25565的是Minecraft的服务器端

回到``WebUI``界面刷新一下就能看到刚刚创建好的两个隧道了，我们分别双击，然后回到终端的日志界面

![](/uploads/posts/Minecraft-server/Image_146585201484185.png)

如图的红色字符的链接，就是``WebUI``和Minecraft的远程访问链接，将Minecraft对应的复制到游戏中即可连接上



## 结语



大功告成！(笔者服务器出生地的截图 >w<)

![](/uploads/posts/Minecraft-server/792C7ECDA8518FCCDC8FA8E5E4E726CF.png)

