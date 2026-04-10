+++
title = "Deploying a Minecraft Server on Linux (CentOS)"
date = 2025-03-19T18:48:59+08:00
translationKey = "minecraft-server"
tags = ["Server", "Linux", "Minecraft"]
categories = ["Tech", "Practical Tech"]

[params]
toc = true
+++

I recently set up a physical server and wanted to use it to host a Minecraft server. After staying up late researching, I succeeded and am sharing this guide in hopes that it helps everyone, especially Linux users without a public IP environment (like me).

### Reference Websites

[Installing and using Red Hat build of OpenJDK 21 on RHEL | Red Hat Product Documentation](https://docs.redhat.com/zh-cn/documentation/red_hat_build_of_openjdk/21/html-single/installing_and_using_red_hat_build_of_openjdk_21_on_rhel/index#installing-jre-on-rhel-using-yum_openjdk)

[SakuraFrp Launcher Installation / Usage Guide | SakuraFrp Documentation](https://doc.natfrp.com/launcher/usage.html)

[CentOS | Docker Docs](https://docs.docker.com/engine/install/centos/)

[Linux Terminal Server Hosting Tutorial ★ No Panel ★ Minecraft_bilibili](https://www.bilibili.com/video/BV1iv4y1P7wJ/?spm_id_from=333.1007.top_right_bar_window_history.content.click&vd_source=c8beb52bf015e61e5378008c684545a4)

- From the Bilibili uploader ``翱翔大使``, which is the main source of ideas for this whole article.

## Java Configuration

Running Minecraft requires the corresponding version of the Java environment; here I installed OpenJDK 21.

```bash
sudo yum install java-21-openjdk
java -version // verify if successfully installed
```

If the server has multiple Java versions, you can use ``alternatives`` to switch versions.

```bash
alternatives --config java
```

As shown below, we enter ``2`` and press Enter to switch to the required version.

![Screenshot_2025-03-19_191616.png](/uploads/posts/Minecraft-server/Screenshot_2025-03-19_191616.png)

## Game Deployment

First, download the Minecraft server software from the following URL. Here I downloaded Banner (1.20.1), which supports Fabric.

[MohistMC]([MohistMC - Home](https://www.mohistmc.com/))

![](/uploads/posts/Minecraft-server/Screenshot_2025-03-19_185204.png)

![](/uploads/posts/Minecraft-server/Screenshot_2025-03-19_185231.png)

Once downloaded, you will get a file like ``banner-1.20.1-800-server.jar``. Next, open your SSH client to operate on the server:

```bash
cd /home/username // switch to personal directory or desired installation location
mkdir Minecraft // create a folder for the game
cd Minecraft
```

Using the SFTP feature in your SSH client (or any other file transfer method), copy the game file ``banner-1.20.1-800-server.jar`` you just downloaded into the newly created ``/home/username/Minecraft`` folder.

Next, let's write a startup script for the server.

```bash
nano start.sh
```

Fill in the following content, but note the purpose of each parameter:

- ``-Xmx`` is the maximum allocated memory, ``-Xms`` is the minimum allocated memory. I have 32GB of memory and allocated 6GB to the game (feel free to allocate more).
- ``banner-1.20.1-800-server.jar`` is the name of the game file you just downloaded.

```bash
java -Xmx6144M -Xms6144m -jar banner-1.20.1-800-server.jar
stty echo
```

Press ``Ctrl + O`` to write, ``Enter`` to confirm, and ``Ctrl + X`` to exit.

Next, grant execution permissions to ``start.sh`` to avoid permission denied issues.

```bash
chmod 777 start.sh
```

Then install ``screen``. Simply put, ``screen`` is a tool that helps users create independent sessions that can be resumed at any time.

```bash
yum install screen
```

``screen`` has the following common commands:

```bash
screen -S [name] // create a new screen named "name"
screen -ls // list names and ports of all running screens
screen -r [port] // attach to the screen with the specified port
```

Next, create a new ``screen`` to run the script.

```bash
screen -S Minecraft
```

In the newly appeared session, run ``start.sh``.

```bash
./start.sh
```

Then everything should go smoothly. I didn't encounter any errors here. Finally, it comes to ``...EULA...`` asking us to agree to the EULA. Enter ``true`` and press Enter. After a short wait, the game server will run successfully on port ``25565``.

To leave this Minecraft ``screen``, just press ``Ctrl+A+D``.

For game rule changes (like 'whether cracked players are allowed to join'), you need to modify the contents of ``server.properties``.

---

Regarding connection: If it's a cloud server, map the port in the administration panel, then connect to ``domain:port`` in your Minecraft client.

However, for a physical server like mine, or a Linux device, or a personal PC without a public IP, we need to proceed with Intranet Penetration.

## Intranet Penetration

Here I am using ``SakuraFrp``, which is well-known and reliable in the Minecraft community, for intranet penetration. Other tools are mostly similar.

### Docker

``SakuraFrp`` on Linux runs on Docker, so let's deploy Docker first. The operations entirely follow the official documentation.

```bash
sudo dnf -y install dnf-plugins-core
sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
```

I encountered very slow installation speeds and download failures here. Running the command again solved the problem.

```bash
sudo dnf install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

After the installation is complete:

```bash
sudo systemctl enable --now docker
```

```bash
sudo docker run hello-world
```

The ``run hello-world`` test above is very likely to fail. Let's solve this issue by referring to the following two articles:

[[Complete Solution] Failed to run hello-world image after Docker installation: Unable to find image 'hello-world:latest' locally - CSDN Blog](https://blog.csdn.net/Fengdf666/article/details/140236208)

[Failed or Timeout Running hello-world Image in Docker - Paul7777 - cnblogs](https://www.cnblogs.com/paul-liang/p/18384633)

Combining the two above will eventually solve the problem. First, let's configure the ``daemon`` file.

```bash
nano /etc/docker/daemon.json
```

Copy the following content into it:

- At the time of my testing (2025/3/19), the following mirrors are still working.

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

Save + Exit. Next, restart docker, and execute the test once more.

```bash
sudo systemctl daemon-reload
sudo systemctl restart docker
docker run hello-world
```

I successfully installed docker up to this point. If the test still fails, please check the content of ``daemon.json`` to see if there are missing or extra commas and brackets.

### SakuraFrp

For deploying ``SakuraFrp`` on Linux, the official documentation provides a detailed solution.

![](/uploads/posts/Minecraft-server/Screenshot_2025-03-19_203047.png)

First, run the following command as an administrator in the terminal:

```bash
sudo bash -c ". <(curl -sSL https://doc.natfrp.com/launcher.sh)"
```

After installation, it should automatically output logs and prompt you to fill in the access token. This (or the subsequent operations) can be found in the management panel on the ``SakuraFrp`` official website.

![](/uploads/posts/Minecraft-server/Screenshot_2025-03-19_203530.png)

After logging in, you will be able to see its log files. Below are the common operations to start it and view logs:

```bash
docker start natfrp-service
docker logs natfrp-service
```

As shown below, we now need to physically operate the server.

![](/uploads/posts/Minecraft-server/Image_146159838978722.png)

Open a browser (Linux usually comes with Firefox) and access the URL after "Usage" to open the ``WebUI``.

Then you will see there is nothing under "Tunnels", only a plus sign. At this time, we enter the ``SakuraFrp`` management panel, find ``Tunnel List`` under Services, and create two new tunnels as shown below:

![](/uploads/posts/Minecraft-server/Screenshot_2025-03-19_204855.png)

![](/uploads/posts/Minecraft-server/Screenshot_2025-03-19_205010.png)

The first one with port 7102 is the ``WebUI`` for ``SakuraFrp`` on the server, intended for remote management.

The second one with port 25565 is for the Minecraft server.

Return to the ``WebUI`` interface and refresh, you will see the two tunnels just created. Double-click them respectively, and then go back to the terminal log interface.

![](/uploads/posts/Minecraft-server/Image_146585201484185.png)

The links in red characters as shown in the image are the remote access links for the ``WebUI`` and Minecraft. Just copy the Minecraft one into the game, and you can connect to it.

## Conclusion

We are done! (A screenshot of my server's spawn point >w<)

![](/uploads/posts/Minecraft-server/792C7ECDA8518FCCDC8FA8E5E4E726CF.png)
