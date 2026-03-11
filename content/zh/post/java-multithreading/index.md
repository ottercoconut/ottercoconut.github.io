+++
title: Java 多线程
date: 2025-03-21T14:50:07+08:00
translationKey: java-multithreading
tags: [Java, 并发, 多线程, JVM]
categories: [技术, 后端开发]

[params]
toc = true
+++

### 参考网站

[多线程 - Java教程 - 廖雪峰的官方网站](https://liaoxuefeng.com/books/java/threading/index.html)

> 多数参考了廖老师的博客 非常好教程

[万字图解Java多线程 - 个人文章 - SegmentFault 思否](https://segmentfault.com/a/1190000023960592)

> 相对没那么详细，就讲到同步锁和线程池，简洁清晰
>
> 也补充了一些知识，例如线程状态，同步锁，生产者消费者模型......

## Java 多线程

#### 进程/线程

进程和线程的关系： **一个进程可以包含一个或多个线程** ，但至少会有一个线程。

操作系统调度的 **最小任务单位** 其实不是进程，而是线程。常用的Windows、Linux等操作系统都采用抢占式多任务，如何调度线程完全由操作系统决定，程序自己不能决定什么时候执行，以及执行多长时间。

多任务既可以由多进程实现，也可以由单进程内的多线程实现，还可以混合多进程＋多线程

和多线程相比，多进程的缺点在于：

- 创建进程比创建线程 **开销** 大，尤其是在Windows系统上
- 进程间通信比线程间通信要慢，因为线程间通信就是读写同一个变量，速度很快

多进程的优点在于：

- 多进程 **稳定性** 比多线程高，因为在多进程的情况下，一个进程崩溃不会影响其他进程
- 在多线程的情况下，任何一个线程崩溃会直接导致整个进程崩溃



#### 多线程

Java语言内置了多线程支持：一个Java程序实际上是一个 **JVM进程** ，JVM进程用一个主线程来执行`main()`方法，在`main()`方法内部，我们又可以启动多个线程。此外，JVM还有负责垃圾回收的其他工作线程等。

和单线程相比，多线程编程的特点在于：多线程经常需要 **读写共享数据，并且需要同步** 。

例如，播放电影时，就必须由一个线程播放视频，另一个线程播放音频，两个线程需要协调运行，否则画面和声音就不同步。因此，多线程编程的复杂度高，调试更困难。



### 创建多线程

[创建新线程 - Java教程 - 廖雪峰的官方网站](https://liaoxuefeng.com/books/java/threading/new-thread/index.html)

要创建一个新线程非常容易，我们需要实例化一个`Thread`实例，然后调用它的`start()`方法：

```java
public class Main {
    public static void main(String args[]) {
        Thread t = new Thread();
        t.start();
    }
}
```

令新线程能执行指定的代码，有以下几种方法：

**方法一** ：从`Thread`派生一个自定义类，然后覆写`run()`方法：

```java
public class Main {
    public static void main(String args[]) {
        Thread t = new Thread();
        t.start();
    }
}
class MyThread extends Thread {
    @Overread
    public void run(){
    	System.out.println("start new thread!");
    }
}
```

执行上述代码，注意到`start()`方法会在内部自动调用实例的`run()`方法。



**方法二** ：创建`Thread`实例时，传入一个`Runnable`实例

```java
public class Main {
    public static void main(String[] args) {
        Thread t = new Thread(new MyRunnable());
        t.start(); // 启动新线程
    }
}
class MyRunnable implements Runnable {
    @Override
    public void run() {
        System.out.println("start new thread!");
    }
}
```

或者用Java 8引入的lambda语法进一步简写为：

```java
public class Main {
    public static void main(String[] args) {
        Thread t = new Thread(() -> {
            System.out.println("start new thread!");
        });
        t.start(); // 启动新线程
    }
}
```

但是，直接调用 ``run()`` 方法，并不能实现多线程，当前线程也不会改变，而只是执行 ``run()`` 方法

> 必须调用`Thread`实例的`start()`方法才能启动新线程，如果我们查看`Thread`类的源代码，会看到`start()`方法内部调用了一个`private native void start0()`方法，`native`修饰符表示这个方法是由JVM虚拟机内部的C代码实现的，不是由Java代码实现的。

---



使用线程和直接在 ``main()`` 方法中执行的 **区别** ：

```Java
public class Main {
    public static void main(String[] args) {
        System.out.println("main start...");
        Thread t = new Thread() {
            public void run() {
                System.out.println("thread run...");
                System.out.println("thread end.");
            }
        };
        t.start();
        System.out.println("main end...");
    }
}
```

``main`` 中命令执行顺序：

- 打印 ``main start...`` 

- 创建 ``Thread`` 对象

- ``start`` 启动新线程

- > 当`start()`方法被调用时，JVM就创建了一个新线程，我们通过实例变量`t`来表示这个新线程对象，并开始执行。

- 打印 ``main end...`` 

但是，在 ``t`` 线程开始运行后， ``main`` 和 ``t`` 就 **同时运行** 了，此时程序本身无法确定线程的调度顺序

要模拟并发执行的效果，我们可以在线程中调用`Thread.sleep()`，参数的单位是毫秒， ``sleep()`` 强迫当前线程 **暂停** 一段时间：

```java
public class Main {
    public static void main(String[] args) {
        System.out.println("main start...");
        Thread t = new Thread() {
            public void run() {
                System.out.println("thread run...");
                try {
                    Thread.sleep(10);
                } catch (InterruptedException e) {}
                System.out.println("thread end.");
            }
        };
        t.start();
        try {
            Thread.sleep(20);
        } catch (InterruptedException e) {}
        System.out.println("main end...");
    }
}
```



#### 线程的优先级

```java
Thread.setPriority(int n) //默认为5
```

JVM自动把1（低）~10（高）的优先级映射到操作系统实际优先级上（不同操作系统有不同的优先级数量）。优先级高的线程被操作系统调度的优先级较高，操作系统对高优先级线程可能调度更频繁，但我们 **决不能通过设置优先级来确保高优先级的线程一定会先执行** 。cpu比较忙时，优先级高的线程获取更多的时间片，cpu比较闲时，优先级设置基本没用



 `yield()` 方法会让运行中的线程切换到就绪状态，重新争抢cpu的时间片，争抢时是否获取到时间片看cpu的分配。

```java
public static native void yield();

Runnable r1 = () -> {
    int count = 0;
    for (;;){
       log.info("---- 1>" + count++);
    }
};
Runnable r2 = () -> {
    int count = 0;
    for (;;){
        Thread.yield();
        log.info("            ---- 2>" + count++);
    }
};
Thread t1 = new Thread(r1,"t1");
Thread t2 = new Thread(r2,"t2");
t1.start();
t2.start();
```

```bash
// 运行结果
11:49:15.796 [t1] INFO thread.TestYield - ---- 1>129504
11:49:15.796 [t1] INFO thread.TestYield - ---- 1>129505
11:49:15.796 [t1] INFO thread.TestYield - ---- 1>129506
11:49:15.796 [t1] INFO thread.TestYield - ---- 1>129507
11:49:15.796 [t1] INFO thread.TestYield - ---- 1>129508
11:49:15.796 [t1] INFO thread.TestYield - ---- 1>129509
11:49:15.796 [t1] INFO thread.TestYield - ---- 1>129510
11:49:15.796 [t1] INFO thread.TestYield - ---- 1>129511
11:49:15.796 [t1] INFO thread.TestYield - ---- 1>129512
11:49:15.798 [t2] INFO thread.TestYield -             ---- 2>293
11:49:15.798 [t1] INFO thread.TestYield - ---- 1>129513
11:49:15.798 [t1] INFO thread.TestYield - ---- 1>129514
11:49:15.798 [t1] INFO thread.TestYield - ---- 1>129515
11:49:15.798 [t1] INFO thread.TestYield - ---- 1>129516
11:49:15.798 [t1] INFO thread.TestYield - ---- 1>129517
11:49:15.798 [t1] INFO thread.TestYield - ---- 1>129518
```

如上述结果所示，t2线程每次执行时进行了yield()，线程1执行的机会明显比线程2要多。



#### 小结

- Java用`Thread`对象表示一个线程，通过调用`start()`启动一个新线程
- 一个线程对象只能调用一次`start()`方法
- 线程的执行代码写在`run()`方法中
- 线程调度由操作系统决定，程序本身无法决定调度顺序
- `Thread.sleep()`可以把当前线程暂停一段时间

---

### 线程的阻塞



使得线程阻塞的方式有下面几种：

- BIO阻塞，即使用了阻塞式的io流
- sleep(long time) 让线程休眠进入阻塞状态
- a.join() 调用该方法的线程进入阻塞，等待a线程执行完恢复运行
- sychronized或ReentrantLock 造成线程未获得锁进入阻塞状态
- 获得锁之后调用wait()方法 也会让线程进入阻塞状态
- LockSupport.park() 让线程进入阻塞状态



####  `Thread.sleep()` 

 使线程休眠，会将运行中的线程进入阻塞状态。当休眠时间结束后，重新争抢cpu的时间片继续运行

```java
// 方法的定义 native方法
public static native void sleep(long millis) throws InterruptedException; 

try {
   // 休眠2秒
   // 该方法会抛出 InterruptedException异常 即休眠过程中可被中断，被中断后抛出异常
   Thread.sleep(2000);
 } catch (InterruptedException异常 e) {
 }
 try {
   // 使用TimeUnit的api可替代 Thread.sleep 
   TimeUnit.SECONDS.sleep(1);
 } catch (InterruptedException e) {
 }

```



####  `Thread.join()`

一个线程还可以等待另一个线程直到其运行结束。例如，`main`线程在启动`t`线程后，可以通过`t.join()`等待`t`线程结束后再继续运行：

```java
public class Main {
    public static void main(String[] args) throws InterruptedException {
        Thread t = new Thread(() -> {
            System.out.println("hello");
        });	//java8 lambda方式
        System.out.println("start");
        t.start(); // 启动t线程
        t.join(); // 此处main线程会等待t结束
        System.out.println("end");
    }
}
```

当`main`线程对线程对象`t`调用`join()`方法时，主线程将等待变量`t`表示的线程运行结束，即`join`就是指等待该线程结束， **然后才继续往下执行自身线程** 。所以，上述代码打印顺序可以肯定是`main`线程先打印`start`，`t`线程再打印`hello`，`main`线程最后再打印`end`。

如果`t`线程已经结束，对实例`t`调用`join()`会立刻返回。此外，`join(long)`的重载方法也可以指定一个等待时间，超过等待时间后就不再继续等待。



#### 小结

- **线程阻塞的常见方式**：BIO阻塞、`sleep()`、`join()`、未获取锁（`synchronized`/`ReentrantLock`）、`wait()`、`LockSupport.park()`。
-  `sleep()` ：让线程休眠指定时间，可被中断，推荐用`TimeUnit`增强可读性。
-  `join()` ：让当前线程等待目标线程执行完毕，常用于控制线程执行顺序。
- **阻塞与恢复**：线程进入阻塞后，需等待特定条件（如时间结束、锁释放、目标线程完成）才能恢复运行。

---



### 中断线程

[中断线程 - Java教程 - 廖雪峰的官方网站](https://liaoxuefeng.com/books/java/threading/interrupt/index.html)

如果线程需要执行一个长时间任务，就可能需要能中断线程。中断线程就是其他线程给该线程发一个信号，该线程收到信号后结束执行`run()`方法，使得自身线程能立刻结束运行。

例如，从网络下载一个100M的文件，如果网速很慢，用户等得不耐烦，就可能在下载过程中点“取消”，这时，程序就需要中断下载线程的执行。

####   `Thread.interrupt`

中断一个线程非常简单，只需要在其他线程中对目标线程调用`interrupt()`方法，目标线程需要反复检测自身状态是否是interrupted状态， **如果是，就立刻结束运行** 。

```java
public class Main {
    public static void main(String[] args) throws InterruptedException {
        Thread t = new MyThread();
        t.start();
        Thread.sleep(1); // 暂停1毫秒
        t.interrupt(); // 中断t线程
        t.join(); // 等待t线程结束
        System.out.println("end");
    }
}

class MyThread extends Thread {
    public void run() {
        int n = 0;
        while (! isInterrupted()) {
            n++;
            System.out.println(n + " hello!");
        }
    }
}
```

上述代码，`main`线程通过调用`t.interrupt()`方法中断`t`线程，但是要注意，`interrupt()`方法 **仅仅向`t`线程发出了“中断请求”** ，至于`t`线程 **是否能立刻响应，要看具体代码** 。而`t`线程的`while`循环会检测`isInterrupted()`，所以上述代码能正确响应`interrupt()`请求，使得自身立刻结束运行`run()`方法。

如果线程处于等待状态，例如，`t.join()`会让`main`线程进入等待状态，此时，如果对`main`线程调用`interrupt()`， **`join()`方法会立刻抛出`InterruptedException`** ，因此，目标线程只要捕获到`join()`方法抛出的`InterruptedException`，就说明有其他线程对其调用了`interrupt()`方法，通常情况下该线程应该立刻结束运行。

```java
public class Main {
    public static void main(String[] args) throws InterruptedException {
        Thread t = new MyThread();
        t.start();
        Thread.sleep(1000);
        t.interrupt(); // 中断t线程
        t.join(); // 等待t线程结束
        System.out.println("end");
    }
}

class MyThread extends Thread {
    public void run() {
        Thread hello = new HelloThread();
        hello.start(); // 启动hello线程
        try {
            hello.join(); // 等待hello线程结束
        } catch (InterruptedException e) {
            System.out.println("interrupted!");
        }
        hello.interrupt();
    }
}

class HelloThread extends Thread {
    public void run() {
        int n = 0;
        while (!isInterrupted()) {
            n++;
            System.out.println(n + " hello!");
            try {
                Thread.sleep(100);
            } catch (InterruptedException e) {
                break;
            }
        }
    }
}
```

- `main`线程通过调用`t.interrupt()`从而通知`t`线程中断
- 此时`t`线程正位于`hello.join()`的等待中，此方法会立刻结束等待并抛出`InterruptedException`
- 在`t`线程中捕获了`InterruptedException`，准备结束该线程
- `t`线程结束前，对`hello`线程也进行了`interrupt()`调用通知其中断



####  `running`标志位

另一个常用的中断线程的方法是设置标志位。我们通常会用一个`running`标志位来标识线程是否应该继续运行，在外部线程中，通过把`HelloThread.running`置为`false`，就可以让线程结束：

```java
public class Main {
    public static void main(String[] args)  throws InterruptedException {
        HelloThread t = new HelloThread();
        t.start();
        Thread.sleep(1);
        t.running = false; // 标志位置为false
    }
}

class HelloThread extends Thread {
    public volatile boolean running = true;
    public void run() {
        int n = 0;
        while (running) {
            n ++;
            System.out.println(n + " hello!");
        }
        System.out.println("end!");
    }
}
```

注意到`HelloThread`的标志位`boolean running`是一个 **线程间共享的变量** 。线程间共享变量需要使用`volatile`关键字标记，确保 **每个线程都能读取到更新后的变量值** 。



####  `volatile` 的用处

为什么要对线程间共享的变量用关键字`volatile`声明？这涉及到Java的内存模型。在Java虚拟机中，变量的值保存在主内存中，但是，当线程访问变量时，它会先获取一个副本，并保存在自己的工作内存中。如果线程修改了变量的值，虚拟机会在某个时刻把修改后的值回写到主内存，但是， **这个时间是不确定的** ！

```java
// 这图画得真有水平罢 
┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
           Main Memory
│                               │
   ┌───────┐┌───────┐┌───────┐
│  │ var A ││ var B ││ var C │  │
   └───────┘└───────┘└───────┘
│     │ ▲               │ ▲     │
 ─ ─ ─│─│─ ─ ─ ─ ─ ─ ─ ─│─│─ ─ ─
      │ │               │ │
┌ ─ ─ ┼ ┼ ─ ─ ┐   ┌ ─ ─ ┼ ┼ ─ ─ ┐
      ▼ │               ▼ │
│  ┌───────┐  │   │  ┌───────┐  │
   │ var A │         │ var C │
│  └───────┘  │   │  └───────┘  │
   Thread 1          Thread 2
└ ─ ─ ─ ─ ─ ─ ┘   └ ─ ─ ─ ─ ─ ─ ┘
```

这会导致如果一个线程更新了某个变量，另一个线程读取的值可能还是更新前的。

例如，主内存的变量`a = true`，线程1执行`a = false`时，它在此刻仅仅是把变量`a`的副本变成了`false`，主内存的变量`a`还是`true`，在JVM把修改后的`a`回写到主内存之前，其他线程读取到的`a`的值仍然是`true`，这就造成了 **多线程之间共享的变量不一致** 。

因此，`volatile`关键字的目的是告诉虚拟机：

- 每次访问变量时，总是获取主内存的最新值；
- 每次修改变量后，立刻回写到主内存。

`volatile`关键字解决的是可见性问题：当一个线程 **修改了某个共享变量的值，其他线程能够立刻看到修改后的值** 。

如果我们去掉`volatile`关键字，运行上述程序，发现效果和带`volatile`差不多，这是因为在x86的架构下，JVM回写主内存的速度非常快，但是，换成ARM的架构，就会有显著的延迟。



#### 小结

对目标线程调用`interrupt()`方法可以请求中断一个线程，目标线程通过检测`isInterrupted()`标志获取自身是否已中断。如果目标线程处于等待状态，该线程会捕获到`InterruptedException`；

目标线程检测到`isInterrupted()`为`true`或者捕获了`InterruptedException`都应该立刻结束自身线程；

通过标志位判断需要正确使用`volatile`关键字；

`volatile`关键字解决了共享变量在线程间的可见性问题。

---



### 线程状态

[万字图解Java多线程 - 个人文章 - SegmentFault 思否](https://segmentfault.com/a/1190000023960592#item-2)

[线程的状态 - Java教程 - 廖雪峰的官方网站](https://liaoxuefeng.com/books/java/threading/state/index.html)



#### 系统 - 五种状态

线程的状态可从 操作系统层面分为五种状态

![](java-multithreading/thread-status-1.png)



1. 初始状态：创建线程对象时的状态
2. 可运行状态(就绪状态)：调用 `start()` 方法后进入就绪状态，也就是准备好被cpu调度执行
3. 运行状态：线程获取到cpu的时间片， 执行 `run()` 方法的逻辑
4. 阻塞状态: 线程被阻塞，放弃cpu的时间片，等待解除阻塞重新回到就绪状态争抢时间片
5. 终止状态: 线程执行完成或抛出异常后的状态



#### Java - 六种状态

在Java程序中，一个线程对象只能调用一次`start()`方法启动新线程，并在新线程中执行`run()`方法。一旦`run()`方法执行完毕，线程就结束了。因此，Java线程的状态有以下几种：

![](java-multithreading/thread-status-2.png)

1. NEW 线程对象被创建
2. Runnable 线程调用了 `start()` 方法后进入该状态，该状态包含了三种情况
   1. 就绪状态 :等待cpu分配时间片
   2. 运行状态:进入Runnable方法执行任务
   3. 阻塞状态:BIO 执行阻塞式io流时的状态
3. Blocked 没获取到锁时的阻塞状态(同步锁章节会细说)
4. WAITING 调用 `wait()`  `join()` 等方法后的状态
5. TIMED_WAITING 调用 `sleep(time)`  `wait(time)`  `join(time)` 等方法后的状态
6. TERMINATED 线程执行完成或抛出异常后的状态

![](java-multithreading/thread-status-3.png)

当线程启动后，它可以在`Runnable`、`Blocked`、`Waiting`和`Timed Waiting`这几个状态之间切换，直到最后变成`Terminated`状态，线程终止。

线程终止的原因有：

- 线程正常终止：`run()`方法执行到`return`语句返回；
- 线程意外终止：`run()`方法因为未捕获的异常导致线程终止；
- 对某个线程的`Thread`实例调用`stop()`方法强制终止（强烈不推荐使用）。



#### Thread类中的核心方法

| 方法名称          | 是否static | 方法说明                                                     |
| ----------------- | ---------- | ------------------------------------------------------------ |
| start()           | 否         | 让线程启动，进入就绪状态,等待cpu分配时间片                   |
| run()             | 否         | 重写Runnable接口的方法,线程获取到cpu时间片时执行的具体逻辑   |
| yield()           | 是         | 线程的礼让，使得获取到cpu时间片的线程进入就绪状态，重新争抢时间片 |
| sleep(time)       | 是         | 线程休眠固定时间，进入阻塞状态，休眠时间完成后重新争抢时间片,休眠可被打断 |
| join()/join(time) | 否         | 调用线程对象的join方法，调用者线程进入阻塞,等待线程对象执行完或者到达指定时间才恢复，重新争抢时间片 |
| isInterrupted()   | 否         | 获取线程的打断标记，true:被打断，false：没有被打断。调用后不会修改打断标记 |
| interrupt()       | 否         | 打断线程，抛出InterruptedException异常的方法均可被打断，但是打断后不会修改打断标记，正常执行的线程被打断后会修改打断标记 |
| interrupted()     | 否         | 获取线程的打断标记。调用后会清空打断标记                     |
| stop()            | 否         | 停止线程运行 不推荐                                          |
| suspend()         | 否         | 挂起线程 不推荐                                              |
| resume()          | 否         | 恢复线程运行 不推荐                                          |
| currentThread()   | 是         | 获取当前线程                                                 |

Object中与线程相关方法

| 方法名称                  | 方法说明                               |
| ------------------------- | -------------------------------------- |
| wait()/wait(long timeout) | 获取到锁的线程进入阻塞状态             |
| notify()                  | 随机唤醒被wait()的一个线程             |
| notifyAll();              | 唤醒被wait()的所有线程，重新争抢时间片 |

---



### 守护线程

[守护线程 - Java教程 - 廖雪峰的官方网站](https://liaoxuefeng.com/books/java/threading/daemon/index.html)

Java程序入口就是由JVM启动`main`线程，`main`线程又可以启动其他线程。当所有线程都运行结束时，JVM退出，进程结束。

如果有一个线程没有退出，JVM进程就不会退出。所以，必须保证所有线程都能及时结束。

但是有一种线程的目的就是无限循环，例如，一个定时触发任务的线程：

```java
class TimerThread extends Thread {
    @Override
    public void run() {
        while (true) {
            System.out.println(LocalTime.now());
            try {
                Thread.sleep(1000);
            } catch (InterruptedException e) {
                break;
            }
        }
    }
}
```

如果这个线程不结束，JVM进程就无法结束。问题是，由谁负责结束这个线程？

然而这类线程经常没有负责人来负责结束它们。但是，当其他线程结束时，JVM进程又必须要结束，怎么办？

答案是使用守护线程（Daemon Thread）。

守护线程是指为其他线程服务的线程。在JVM中， **所有非守护线程都执行完毕后** ，无论有没有守护线程，虚拟机都会自动退出。

因此，JVM退出时，不必关心守护线程是否已结束。

如何创建守护线程呢？方法和普通线程一样，只是在调用`start()`方法前， **调用`setDaemon(true)`把该线程标记为守护线程** ：

```java
Thread t = new MyThread();
t.setDaemon(true);
t.start();
```

在守护线程中，编写代码要注意： **守护线程不能持有任何需要关闭的资源** ，例如打开文件等，因为虚拟机退出时，守护线程没有任何机会来关闭文件，这会导致数据丢失。



#### 小结

守护线程是为其他线程服务的线程；

所有非守护线程都执行完毕后，虚拟机退出，守护线程随之结束；

守护线程不能持有需要关闭的资源（如打开文件等）。

---



### 线程同步

[线程同步 - Java教程 - 廖雪峰的官方网站](https://liaoxuefeng.com/books/java/threading/synchronize/index.html)

当多个线程同时运行时，线程的调度由操作系统决定，程序本身无法决定。因此，任何一个线程都有可能在任何指令处被操作系统暂停，然后在某个时间段后继续执行。

这个时候，有个单线程模型下不存在的问题就来了：如果多个线程同时读写共享变量，会出现数据不一致的问题。

我们来看一个例子：

```java
// 多线程
public class Main {
    public static void main(String[] args) throws Exception {
        var add = new AddThread();
        var dec = new DecThread();
        add.start();
        dec.start();
        add.join();
        dec.join();
        System.out.println(Counter.count);
    }
}

class Counter {
    public static int count = 0;
}

class AddThread extends Thread {
    public void run() {
        for (int i=0; i<10000; i++) { Counter.count += 1; }
    }
}

class DecThread extends Thread {
    public void run() {
        for (int i=0; i<10000; i++) { Counter.count -= 1; }
    }
}
```

上面的代码很简单，两个线程同时对一个`int`变量进行操作，一个加10000次，一个减10000次，最后结果应该是0，但是，每次运行，结果实际上都是不一样的。

这是因为对变量进行读取和写入时，结果要正确， **必须保证是原子操作** 。原子操作是指不能被中断的一个或一系列操作。

例如，对于语句：

```java
n = n + 1;
```

看上去是一行语句，实际上对应了3条指令：

```java
ILOAD
IADD
ISTORE
```

我们假设`n`的值是`100`，如果两个线程同时执行`n = n + 1`，得到的结果很可能不是`102`，而是`101`，原因在于：

```java
┌───────┐     ┌───────┐
│Thread1│     │Thread2│
└───┬───┘     └───┬───┘
    │             │
    │ILOAD (100)  │
    │             │ILOAD (100)
    │             │IADD
    │             │ISTORE (101)
    │IADD         │
    │ISTORE (101) │
    ▼             ▼
```

如果线程1在执行`ILOAD`后被操作系统中断，此刻如果线程2被调度执行，它执行`ILOAD`后获取的值仍然是`100`，最终结果被两个线程的`ISTORE`写入后变成了`101`，而不是期待的`102`。

这说明多线程模型下，要保证逻辑正确，对共享变量进行读写时， **必须保证一组指令以原子方式执行：即某一个线程执行时，其他线程必须等待** ：



####  `synchronized 同步锁` 



```java
┌───────┐     ┌───────┐
│Thread1│     │Thread2│
└───┬───┘     └───┬───┘
    │             │
    │-- lock --   │
    │ILOAD (100)  │
    │IADD         │
    │ISTORE (101) │
    │-- unlock -- │
    │             │-- lock --
    │             │ILOAD (101)
    │             │IADD
    │             │ISTORE (102)
    │             │-- unlock --
    ▼             ▼
```

通过加锁和解锁的操作，就能保证3条指令总是在一个线程执行期间，不会有其他线程会进入此指令区间。即使在执行期线程被操作系统中断执行，其他线程也会因为无法获得锁导致无法进入此指令区间。只有执行线程将锁释放后，其他线程才有机会获得锁并执行。这种加锁和解锁之间的代码块我们称之为临界区(Critical Section)，任何时候临界区最多只有一个线程能执行。

可见， **保证一段代码的原子性就是通过加锁和解锁实现的** 。Java程序使用`synchronized`关键字对一个对象进行加锁：

```java
synchronized(lock) {
    n = n + 1;
}
```

`synchronized`保证了代码块在 **任意时刻最多只有一个线程能执行** 。我们把上面的代码用`synchronized`改写如下：

```java
// 多线程
public class Main {
    public static void main(String[] args) throws Exception {
        var add = new AddThread();
        var dec = new DecThread();
        add.start();
        dec.start();
        add.join();
        dec.join();
        System.out.println(Counter.count);
    }
}

class Counter {
    public static final Object lock = new Object();
    public static int count = 0;
}

class AddThread extends Thread {
    public void run() {
        for (int i=0; i<10000; i++) {
            synchronized(Counter.lock) {
                Counter.count += 1;
            }
        }
    }
}

class DecThread extends Thread {
    public void run() {
        for (int i=0; i<10000; i++) {
            synchronized(Counter.lock) {
                Counter.count -= 1;
            }
        }
    }
}
```

注意到代码：

```java
synchronized(Counter.lock) { // 获取锁
    ...
} // 释放锁
```

它表示用`Counter.lock`实例作为锁，两个线程在执行各自的`synchronized(Counter.lock) { ... }`代码块时，必须先获得锁，才能进入代码块进行。执行结束后，在`synchronized`语句块结束会自动释放锁。这样一来，对`Counter.count`变量进行读写就不可能同时进行。上述代码无论运行多少次，最终结果都是0。

使用`synchronized`解决了多线程同步访问共享变量的正确性问题。但是，它的缺点是带来了性能下降。因为`synchronized`代码块无法并发执行。此外，加锁和解锁需要消耗一定的时间，所以，`synchronized`会降低程序的执行效率。

我们来概括一下如何使用`synchronized`：

1. 找出修改共享变量的线程代码块；
2. 选择一个共享实例作为锁；
3. 使用`synchronized(lockObject) { ... }`。

在使用`synchronized`的时候， **不必担心抛出异常** 。因为无论是否有异常，都会在`synchronized`结束处正确释放锁：

```java
public void add(int m) {
    synchronized (obj) {
        if (m < 0) {
            throw new RuntimeException();
        }
        this.value += m;
    } // 无论有无异常，都会在此释放锁
}
```

此外，多个线程各自都可以同时获得锁：因为JVM只保证同一个锁在任意时刻只能被一个线程获取， **但两个不同的锁在同一时刻可以被两个线程分别获取** 。

因此，使用`synchronized`的时候， **获取到的是哪个锁非常重要** 。锁对象如果不对，代码逻辑就不对。

下面是应用了两个不同的锁来提升效率的示例：

```java
public class Main {
    public static void main(String[] args) throws Exception {
        var ts = new Thread[] { new AddStudentThread(), new DecStudentThread(), new AddTeacherThread(), new DecTeacherThread() };
        for (var t : ts) {
            t.start();
        }
        for (var t : ts) {
            t.join();
        }
        System.out.println(Counter.studentCount);
        System.out.println(Counter.teacherCount);
    }
}

class Counter {
    public static final Object lockStudent = new Object();
    public static final Object lockTeacher = new Object();
    public static int studentCount = 0;
    public static int teacherCount = 0;
}

class AddStudentThread extends Thread {
    public void run() {
        for (int i=0; i<10000; i++) {
            synchronized(Counter.lockStudent) {
                Counter.studentCount += 1;
            }
        }
    }
}

class DecStudentThread extends Thread {
    public void run() {
        for (int i=0; i<10000; i++) {
            synchronized(Counter.lockStudent) {
                Counter.studentCount -= 1;
            }
        }
    }
}

class AddTeacherThread extends Thread {
    public void run() {
        for (int i=0; i<10000; i++) {
            synchronized(Counter.lockTeacher) {
                Counter.teacherCount += 1;
            }
        }
    }
}

class DecTeacherThread extends Thread {
    public void run() {
        for (int i=0; i<10000; i++) {
            synchronized(Counter.lockTeacher) {
                Counter.teacherCount -= 1;
            }
        }
    }
}
```



#### 不需要 `synchronized` 的操作

JVM规范定义了几种原子操作：

- 基本类型（`long`和`double`除外）赋值，例如：`int n = m`；
- 引用类型赋值，例如：`List<String> list = anotherList`。

`long`和`double`是64位数据，JVM没有明确规定64位赋值操作是不是一个原子操作，不过在x64平台的JVM是把`long`和`double`的赋值作为原子操作实现的。

单条原子操作的语句不需要同步。例如：

```java
public void set(int m) {
    synchronized(lock) {
        this.value = m;
    }
}
```

就不需要同步。

对引用也是类似。例如：

```java
public void set(String s) {
    this.value = s;
}
```

上述 **赋值语句** 并不需要同步。

但是，如果是 **多行赋值语句，就必须保证是同步操作** ，例如：

```java
class Point {
    int x;
    int y;
    public void set(int x, int y) {
        synchronized(this) {
            this.x = x;
            this.y = y;
        }
    }
    public int[] get() {
        synchronized(this) {
            return new int[]{x,y};
        }
    }
}
```

上面的读写，即( set(), get() )需要同步，在读的时候若是不同步，会造成程序的逻辑错误：

```java
public int[] get() {
        int[] copy = new int[2];
        copy[0] = x;
        copy[1] = y;
    }
```

假定当前坐标是`(100, 200)`，那么当设置新坐标为`(110, 220)`时，上述未同步的多线程读到的值可能有：

- (100, 200)：x，y更新前；
- (110, 200)：x更新后，y更新前；
- (110, 220)：x，y更新后。

如果读取到`(110, 200)`，即读到了更新后的x，更新前的y，无法保证读取的多个变量状态保持一致。

有些时候，通过一些巧妙的转换，可以把非原子操作变为原子操作。例如，上述代码如果改造成：

```java
class Point {
    int[] ps;
    public void set(int x, int y) {
        int[] ps = new int[] { x, y };
        this.ps = ps;
    }
}
```

就不再需要写同步，因为`this.ps = ps`是引用赋值的原子操作。而语句：

```java
int[] ps = new int[] { x, y };
```

这里的`ps`是方法内部定义的局部变量，每个线程都会有各自的局部变量，互不影响，并且互不可见，并不需要同步。

不过要注意，读方法在复制`int[]`数组的过程中仍然需要同步。



#### 不可变对象无需同步

不可变对象是指**创建后状态不能被修改的对象**。在 Java 中，典型的不可变对象包括：

- `String`
- `List.of()` 创建的不可变集合（Java 9+）
- 基本类型的包装类（如 `Integer`, `Long` 等）

如果多线程读写的是一个不可变对象，那么无需同步，因为不会修改对象的状态：

```java
class Data {
    List<String> names;
    void set(String[] names) {
        this.names = List.of(names);
    }
    List<String> get() {
        return this.names;
    }
}
```

注意到`set()`方法内部创建了一个不可变`List`，这个`List`包含的对象也是不可变对象`String`，因此，整个`List<String>`对象都是不可变的，因此读写均无需同步。

分析变量是否能被多线程访问时，首先要理清概念，多线程同时执行的是方法。对于下面这个例子：

```java
class Status {
    List<String> names;
    int x;
    int y;
    void set(String[] names, int n) {
        List<String> ns = List.of(names);
        this.names = ns;
        int step = n * 10;
        this.x += step;
        this.y += step;
    }
    StatusRecord get() {
        return new StatusRecord(this.names, this.x, this.y);
    }
}
```

如果有A、B两个线程，同时执行是指：

- 可能同时执行set()；
- 可能同时执行get()；
- 可能A执行set()，同时B执行get()。

类的成员变量`names`、`x`、`y`显然能被多线程同时读写，但局部变量（包括方法参数）如果没有“逃逸”，那么只有当前线程可见。局部变量`step`仅在`set()`方法内部使用，因此每个线程同时执行set时都有一份独立的step存储在线程的栈上，互不影响，

局部变量`ns`虽然每个线程也各有一份，但后续赋值` this.names = ns` 对其他线程就变成可见了。对`set()`方法同步时，如果要最小化`synchronized`代码块，可以改写如下：

```java
void set(String[] names, int n) {
    // 局部变量其他线程不可见:
    List<String> ns = List.of(names);
    int step = n * 10;
    synchronized(this) {
        this.names = ns;
        this.x += step;
        this.y += step;
    }
}
```

因此，深入理解多线程还需理解变量在栈上的存储方式，基本类型和引用类型的存储方式也不同。

| 场景                            | 是否需要同步 | 原因                                            |
| :------------------------------ | :----------- | :---------------------------------------------- |
| 不可变对象（如 `List.of()`）    | 否           | 对象不可变，多线程只能读取，无竞态条件。        |
| 局部变量（如 `step`）           | 否           | 线程私有，栈封闭。                              |
| 成员变量赋值（如 `this.names`） | 是           | 引用可能被多线程同时修改，需同步或 `volatile`。 |
| 复合操作（如 `x += step`）      | 是           | 非原子操作（读取-修改-写入），需同步。          |



#### 小结

多线程同时读写共享变量时，可能会造成逻辑错误，因此需要通过`synchronized`同步；

同步的本质就是给指定对象加锁，加锁后才能继续执行后续代码；

注意加锁对象必须是同一个实例；

对JVM定义的单个原子操作不需要同步。

---



### 线程同步方法



#### 线程安全

如果一个类被设计为允许多线程正确访问，我们就说这个类就是“线程安全”的（thread-safe），Java标准库的`java.lang.StringBuffer`也是线程安全的。

还有一些 **不变类** ，例如`String`，`Integer`，`LocalDate`，它们的所有成员变量都是`final`，多线程同时访问时只能读不能写，这些不变类也是线程安全的。

最后，类似`Math`这些 **只提供静态方法，没有成员变量的类** ，也是线程安全的。

除了上述几种少数情况，大部分类，例如`ArrayList`，都是 **非线程安全的类** ，我们不能在多线程中修改它们。但是，如果所有线程都 **只读取，不写入** ，那么`ArrayList`是可以安全地在线程间共享的。

>没有特殊说明时，一个类 **默认是非线程安全的** 。

例如下面的Counter类：

```java
public class Counter {
    private int count = 0;

    public void add(int n) {
        synchronized(this) {
            count += n;
        }
    }

    public void dec(int n) {
        synchronized(this) {
            count -= n;
        }
    }

    public int get() {
        return count;
    }
}
```

这样一来，线程调用`add()`、`dec()`方法时，它不必关心同步逻辑，因为`synchronized`代码块在`add()`、`dec()`方法内部。并且，我们注意到，**`synchronized`锁住的对象是`this`，即当前实例，这又使得创建多个`Counter`实例的时候，它们之间互不影响，可以并发执行**



####  `synchronized` 修饰

我们再观察`Counter`的代码：

```java
public class Counter {
    public void add(int n) {
        synchronized(this) {
            count += n;
        }
    }
    ...
}
```

当我们锁住的是`this`实例时，实际上可以用`synchronized`修饰这个方法。下面两种写法是等价的：

```java
public void add(int n) {
    synchronized(this) { // 锁住this
        count += n;
    } // 解锁
}
```

写法二：

```java
public synchronized void add(int n) { // 锁住this
    count += n;
} // 解锁
```

因此， **用`synchronized`修饰的方法就是同步方法** ，它表示整个方法都必须用`this`实例加锁。



对于`static`方法，是没有`this`实例的，因为`static`方法是针对类而不是实例。但是我们注意到任何一个类都有一个由JVM自动创建的`Class`实例，因此， **对`static`方法添加`synchronized`，锁住的是该类的`Class`实例** 。上述`synchronized static`方法实际上相当于：

```java
public class Counter {
    public static void test(int n) {
        synchronized(Counter.class) {
            ...
        }
    }
}
```



#### 小结

用`synchronized`修饰方法可以把整个方法变为同步代码块，`synchronized`方法加锁对象是`this`；

通过合理的设计和数据封装可以让一个类变为“线程安全”；

一个类没有特殊说明，默认不是thread-safe；

多线程能否安全访问某个非线程安全的实例，需要具体问题具体分析。

---



### 死锁



#### 可重入锁

Java的线程锁是可重入的锁。

什么是可重入的锁？我们还是来看例子：

```java
public class Counter {
    private int count = 0;

    public synchronized void add(int n) {
        if (n < 0) {
            dec(-n);
        } else {
            count += n;
        }
    }

    public synchronized void dec(int n) {
        count += n;
    }
}
```

执行流程：

1. 调用`add(-1)`：
   - 获取`this`锁：计数器=1，持有线程=当前线程
2. 进入`add`方法后调用`dec(1)`：
   - 再次获取`this`锁：发现当前线程已持有，计数器增加到2
3. 退出`dec`方法：
   - 计数器减到1
4. 退出`add`方法：
   - 计数器减到0，真正释放锁

观察`synchronized`修饰的`add()`方法，一旦线程执行到`add()`方法内部，说明它已经获取了当前实例的`this`锁。如果传入的`n < 0`，将在`add()`方法内部调用`dec()`方法。由于`dec()`方法也需要获取`this`锁，现在问题来了：

对同一个线程，能否在获取到锁以后继续获取同一个锁？

答案是肯定的。 **JVM允许同一个线程重复获取同一个锁** ，这种能被同一个线程反复获取的锁，就叫做**可重入锁**。

由于Java的线程锁是可重入锁，所以，获取锁的时候，不但要判断是否是第一次获取，还要记录这是第几次获取。每获取一次锁，记录+1，每退出`synchronized`块，记录-1，减到0的时候，才会真正释放锁。



#### 死锁

一个线程可以获取一个锁后，再继续获取另一个锁。例如：

```java
public void add(int m) {
    synchronized(lockA) { // 获得lockA的锁
        this.value += m;
        synchronized(lockB) { // 获得lockB的锁
            this.another += m;
        } // 释放lockB的锁
    } // 释放lockA的锁
}

public void dec(int m) {
    synchronized(lockB) { // 获得lockB的锁
        this.another -= m;
        synchronized(lockA) { // 获得lockA的锁
            this.value -= m;
        } // 释放lockA的锁
    } // 释放lockB的锁
}
```

在获取多个锁的时候，不同线程获取多个不同对象的锁可能导致死锁。对于上述代码，线程1和线程2如果分别执行`add()`和`dec()`方法时：

- 线程1：进入`add()`，获得`lockA`；
- 线程2：进入`dec()`，获得`lockB`。

随后：

- 线程1：准备获得`lockB`，失败，等待中；
- 线程2：准备获得`lockA`，失败，等待中。

 **此时，两个线程各自持有不同的锁，然后各自试图获取对方手里的锁，造成了双方无限等待下去，这就是死锁。** 

死锁发生后，没有任何机制能解除死锁，只能强制结束JVM进程。

因此，在编写多线程应用时，要特别注意防止死锁。因为死锁一旦形成，就只能强制结束进程。

那么我们应该如何避免死锁呢？答案是： **线程获取锁的顺序要一致** 。即严格按照先获取`lockA`，再获取`lockB`的顺序，改写`dec()`方法如下：

```java
public void dec(int m) {
    synchronized(lockA) { // 获得lockA的锁
        this.value -= m;
        synchronized(lockB) { // 获得lockB的锁
            this.another -= m;
        } // 释放lockB的锁
    } // 释放lockA的锁
}
```



#### 小结

Java的`synchronized`锁是可重入锁；

死锁产生的条件是多线程各自持有不同的锁，并互相试图获取对方已持有的锁，导致无限等待；

避免死锁的方法是多线程获取锁的顺序要一致。

---



###  线程通信

在Java程序中，`synchronized`解决了多线程竞争的问题。例如，对于一个任务管理器，多个线程同时往队列中添加任务，可以用`synchronized`加锁：

```java
class TaskQueue {
    Queue<String> queue = new LinkedList<>();

    public synchronized void addTask(String s) {
        this.queue.add(s);
    }
}
```

但是`synchronized`并没有解决多线程协调的问题。

仍然以上面的`TaskQueue`为例，我们再编写一个`getTask()`方法取出队列的第一个任务：

```java
class TaskQueue {
    Queue<String> queue = new LinkedList<>();

    public synchronized void addTask(String s) {
        this.queue.add(s);
    }

    public synchronized String getTask() {
        while (queue.isEmpty()) {
        }
        return queue.remove();
    }
}
```

上述代码看上去没有问题：`getTask()`内部先判断队列是否为空，如果为空，就循环等待，直到另一个线程往队列中放入了一个任务，`while()`循环退出，就可以返回队列的元素了。

但实际上`while()`循环永远不会退出。因为线程在执行`while()`循环时，已经在`getTask()`入口获取了`this`锁，其他线程根本无法调用`addTask()`，因为`addTask()`执行条件也是获取`this`锁。

因此，执行上述代码，线程会在`getTask()`中因为死循环而100%占用CPU资源。

如果深入思考一下，我们想要的执行效果是：

- 线程1可以调用`addTask()`不断往队列中添加任务；
- 线程2可以调用`getTask()`从队列中获取任务。如果队列为空，则`getTask()`应该等待，直到队列中至少有一个任务时再返回。

 **因此，多线程协调运行的原则就是：当条件不满足时，线程进入等待状态；当条件满足时，线程被唤醒，继续执行任务。** 



####  `wait()`

对于上述`TaskQueue`，我们先改造`getTask()`方法，在条件不满足时，线程进入等待状态：

```java
public synchronized String getTask() {
    while (queue.isEmpty()) {
        this.wait();
    }
    return queue.remove();
}
```

当一个线程执行到`getTask()`方法内部的`while`循环时，它必定已经获取到了`this`锁，此时，线程执行`while`条件判断，如果条件成立（队列为空），线程将执行`this.wait()`，进入等待状态。

这里的关键是：`wait()`方法必须在 **当前获取的锁对象** 上调用，这里获取的是`this`锁，因此调用`this.wait()`。

调用`wait()`方法后，线程进入等待状态，`wait()`方法不会返回，直到将来某个时刻， **线程从等待状态被其他线程唤醒后** ，`wait()`方法才会返回，然后，继续执行下一条语句。

有些仔细的童鞋会指出：即使线程在`getTask()`内部等待，其他线程如果拿不到`this`锁，照样无法执行`addTask()`，肿么办？

这个问题的关键就在于`wait()`方法的执行机制非常复杂。首先，它不是一个普通的Java方法，而是定义在`Object`类的一个`native`方法，也就是由JVM的C代码实现的。其次，必须在`synchronized`块中才能调用`wait()`方法， **因为`wait()`方法调用时，会释放线程获得的锁** ，`wait()`方法返回时，线程又会重新试图获得锁。

因此，只能在锁对象上调用`wait()`方法。因为在`getTask()`中，我们获得了`this`锁，因此，只能在`this`对象上调用`wait()`方法：

```java
public synchronized String getTask() {
    while (queue.isEmpty()) {
        // 释放this锁:
        this.wait();
        // 重新获取this锁
    }
    return queue.remove();
}
```

当一个线程在`this.wait()`等待时，它就会释放`this`锁，从而使得其他线程能够在`addTask()`方法获得`this`锁。



####  `notify()`

现在我们面临第二个问题：如何让等待的线程被 **重新唤醒** ，然后从`wait()`方法返回？答案是在相同的锁对象上调用`notify()`方法。我们修改`addTask()`如下：

```java
public synchronized void addTask(String s) {
    this.queue.add(s);
    this.notify(); // 唤醒在this锁等待的线程
}
```

注意到在往队列中添加了任务后，线程立刻对`this`锁对象调用`notify()`方法，这个方法会唤醒一个正在`this`锁等待的线程（就是在`getTask()`中位于`this.wait()`的线程），从而使得等待线程从`this.wait()`方法返回。

我们来看一个完整的例子(这也是一个生产者消费者模型)：

```java
import java.util.*;

public class Main {
    public static void main(String[] args) throws InterruptedException {
        var q = new TaskQueue();
        var ts = new ArrayList<Thread>();
        for (int i=0; i<5; i++) {
            var t = new Thread() {
                public void run() {
                    // 执行task:
                    while (true) {
                        try {
                            String s = q.getTask();
                            System.out.println("execute task: " + s);
                        } catch (InterruptedException e) {
                            return;
                        }
                    }
                }
            };
            t.start();
            ts.add(t);
        }
        var add = new Thread(() -> {
            for (int i=0; i<10; i++) {
                // 放入task:
                String s = "t-" + Math.random();
                System.out.println("add task: " + s);
                q.addTask(s);
                try { Thread.sleep(100); } catch(InterruptedException e) {}
            }
        });
        add.start();
        add.join();
        Thread.sleep(100);
        for (var t : ts) {
            t.interrupt();
        }
    }
}

class TaskQueue {
    Queue<String> queue = new LinkedList<>();

    public synchronized void addTask(String s) {
        this.queue.add(s);
        this.notifyAll();
    }

    public synchronized String getTask() throws InterruptedException {
        while (queue.isEmpty()) {
            this.wait();
        }
        return queue.remove();
    }
}
```

这个例子中，我们重点关注`addTask()`方法，内部调用了`this.notifyAll()`而不是`this.notify()`，使用`notifyAll()`将唤醒所有当前正在`this`锁等待的线程，而`notify()`只会 **唤醒其中一个** （具体哪个依赖操作系统，有一定的 **随机性**）。这是因为可能有多个线程正在`getTask()`方法内部的`wait()`中等待，使用`notifyAll()`将 **一次性全部唤醒** 。通常来说，`notifyAll()`更安全。有些时候，如果我们的代码逻辑考虑不周，用`notify()`会导致只唤醒了一个线程，而其他线程可能永远等待下去醒不过来了。

但是，注意到`wait()`方法返回时需要 *重新* 获得`this`锁。假设当前有3个线程被唤醒，唤醒后，首先要等待执行`addTask()`的线程结束此方法后，才能释放`this`锁，随后，这3个线程中只能有一个获取到`this`锁，剩下两个将继续等待。

再注意到我们在`while()`循环中调用`wait()`，而不是`if`语句：

```java
public synchronized String getTask() throws InterruptedException {
    if (queue.isEmpty()) {
        this.wait();
    }
    return queue.remove();
}
```

这种写法实际上是错误的，因为线程被唤醒时，需要再次获取`this`锁。多个线程被唤醒后，只有一个线程能获取`this`锁，此刻，该线程执行`queue.remove()`可以获取到队列的元素，然而，剩下的线程如果获取`this`锁后执行`queue.remove()`，此刻队列可能已经没有任何元素了，所以，要始终在`while`循环中`wait()`，并且每次被唤醒后拿到`this`锁就必须再次判断：

```java
while (queue.isEmpty()) {
    this.wait();
}
```



#### 小结

`wait`和`notify`用于多线程协调运行：

- 在`synchronized`内部可以调用`wait()`使线程进入等待状态；
- 必须在已获得的锁对象上调用`wait()`方法；
- 在`synchronized`内部可以调用`notify()`或`notifyAll()`唤醒其他等待线程；
- 必须在已获得的锁对象上调用`notify()`或`notifyAll()`方法；
- 已唤醒的线程还需要重新获得锁后才能继续执行。

---



### 生产者消费者模型

[Java生产者消费者模式的实现和解析_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1tX4y1S7Hz/?spm_id_from=333.1007.top_right_bar_window_history.content.click&vd_source=c8beb52bf015e61e5378008c684545a4)

下面是从B站找来的简单的生产者消费者模型的示例，并不如上面线程通信中的示例以及下面的消息队列模型示例，这三个示例我想就能拿下该模型罢

```java
public class Demo1 {
    /**
     * 交替执行两个线程
     * 一个输出“1,2,3,...”
     * 一个输出“a,b,c,...”
     */
    public static void main(String[] args) {
        Factory factory = new Factory();

        final Thread t1 = new Thread(new Runnable() {
            @Override
            public void run() {
                for(int i = 1;i <= 26;i++){
                    factory.product(i);
                }
            }
        });

        final Thread t2 = new Thread(new Runnable() {
            @Override
            public void run() {
                for(int i = 'a';i <= 'z';i++){
                    factory.consume((char) i);
                }
            }
        });
    t1.start();
    t2.start();
    }
}
```

```java
public class Factory {
    /**
     * 0: 生产者正在生成，消费者正在等待，生产者结束生产后告知消费者进行消费
     * 1: 消费者正在消费，生产者正在等待，消费者结束消费后高职生产者进行生产
     */
    private int sign = 0;	//状态值


    public synchronized void product(int n){
        if(sign == 1){
            try {
                this.wait();
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }
        System.out.print(n);
        this.notify();
        this.sign = 1;
    }

    public synchronized void consume(char c){
        if(sign == 0){
            try {
                this.wait();
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }
        System.out.print(c);
        this.notify();
        this.sign = 0;
    }
}

```

线程的运行有一定随机性，往往用户无法决定，但是生产者消费者模型，能实现两个线程的“交替”运行

注释里的内容不再概述，我们来分析一下：

假设线程 `t1` 先被调用，由于 `sign = 0` ，所以打印字符 `1` ， `sign` 变为1。下面有两种可能，调用线程 `t1` 或 `t2` 

调用 `t1` :

-  `sign = 1` 进入 `try/catch` 
- 同步锁的对象 `this。wait()` 也就是进入 **“等待”** 状态
-  `wait()` 会 **释放锁** ，线程 `t2` 执行，运行 `consume()`
-  `notfiy()`  **唤醒**  `this` 中等待的线程 `t1` 
-  `sign` 被赋值0，周而复始   

调用 `t2` :

- 线程 `t2` 执行，运行 `consume()` 
-  `notify` 不唤醒任一线程(因为无线程处于等待状态)
-  `sign` 被赋值0，周而复始  



#### 示例分析

下面是较复杂(贴切实际)的一种，思想和上面简单的例子差不多的

>  关于下面示例中 `lambda` 表达式创建线程的方式，需要补充几点：
>
> - `new Thread()` - 创建新线程
> - `() -> {...}` - Lambda表达式定义线程任务
> - `"生产者" + i` - 线程命名
> - `.start()` - 启动线程

这里通过循环来创建线程，所以用循环的参数为其命名

```java
  public static void main(String[] args) throws InterruptedException {
        MessageQueue queue = new MessageQueue(2);

        // 三个生产者向队列里存值
        for (int i = 0; i < 3; i++) {
            int id = i;
            new Thread(() -> {
                queue.put(new Message(id, "值" + id));
            }, "生产者" + i).start();
        }

        Thread.sleep(1000);

        // 一个消费者不停的从队列里取值
        new Thread(() -> {
            while (true) {
                queue.take();
            }
        }, "消费者").start();

    }
}

// 消息队列被生产者和消费者持有
class MessageQueue {
    private LinkedList<Message> list = new LinkedList<>();

    // 容量
    private int capacity;

    public MessageQueue(int capacity) {
        this.capacity = capacity;
    }
    //生产者
    public void put(Message message) {
        synchronized (list) {
            while (list.size() == capacity) {
                log.info("队列已满，生产者等待");
                try {
                    list.wait();
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
            }
            list.addLast(message);
            log.info("生产消息:{}", message);
            // 生产后通知消费者
            list.notifyAll();
        }
    }
    //消费者
    public Message take() {
        synchronized (list) {
            while (list.isEmpty()) {
                log.info("队列已空，消费者等待");
                try {
                    list.wait();
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
            }
            Message message = list.removeFirst();
            //从队列头部取出消息
            log.info("消费消息:{}", message);
            // 消费后通知生产者
            list.notifyAll();
            return message;
        }
    }
}
 // 消息
class Message {
    private int id;
    private Object value;
}
```

主函数:

- 创建了一个容量为2的消息队列`MessageQueue`
- 启动3个生产者线程，每个生产者向队列中放入一条消息
- 主线程休眠1秒，让生产者有足够时间开始工作
- 启动一个消费者线程，不断从队列中取出消息

生产者:

- 使用`synchronized`块获取`list`对象的锁
- 检查队列是否已满（`while`循环防止虚假唤醒）
- 如果队列已满，调用`wait()`释放锁并等待
- 当队列有空闲时，添加消息到队列尾部
- 调用`notifyAll()`唤醒可能正在等待的消费者线程

消费者:

- 使用`synchronized`块获取`list`对象的锁
- 检查队列是否为空（`while`循环防止虚假唤醒）
- 如果队列为空，调用`wait()`释放锁并等待
- 当队列有消息时，从队列头部取出消息
- 调用`notifyAll()`唤醒可能正在等待的生产者线程
- 返回取出的消息



#### 小结

1. **同步机制**：使用`synchronized`保证对队列操作的原子性
2. **等待/通知机制**：使用`wait()`和`notifyAll()`实现线程间通信
3. **循环检查条件**：使用`while`而非`if`检查条件，防止虚假唤醒
4. **容量限制**：控制队列大小，防止内存耗尽

---



### 可重入锁 

从Java 5开始，引入了一个高级的处理并发的`java.util.concurrent`包，它提供了大量更高级的并发功能，能大大简化多线程程序的编写。

我们知道Java语言直接提供了`synchronized`关键字用于加锁，但这种锁一是很重，二是获取时必须一直等待，没有额外的尝试机制。

`java.util.concurrent.locks`包提供的`ReentrantLock`用于替代`synchronized`加锁，我们来看一下传统的`synchronized`代码：

```java
public class Counter {
    private int count;

    public void add(int n) {
        synchronized(this) {
            count += n;
        }
    }
}
```

如果用`ReentrantLock`替代，可以把代码改造为：

```java
public class Counter {
    private final Lock lock = new ReentrantLock();
    private int count;

    public void add(int n) {
        lock.lock();
        try {
            count += n;
        } finally {
            lock.unlock();
        }
    }
}
```

因为`synchronized`是Java语言层面提供的语法，所以我们不需要考虑异常，而`ReentrantLock`是Java代码实现的锁，我们就必须先获取锁，然后在`finally`中正确释放锁。

顾名思义，`ReentrantLock`是可重入锁，它和`synchronized`一样，一个线程可以多次获取同一个锁。

和`synchronized`不同的是，`ReentrantLock`可以尝试获取锁：

```java
if (lock.tryLock(1, TimeUnit.SECONDS)) {
    try {
        ...
    } finally {
        lock.unlock();
    }
}
```

上述代码在尝试获取锁的时候，最多等待1秒。如果1秒后仍未获取到锁，`tryLock()`返回`false`，程序就可以做一些额外处理，而不是无限等待下去。

所以，使用`ReentrantLock`比直接使用`synchronized`更安全，线程在`tryLock()`失败的时候不会导致死锁。



下面来介绍一下它的各种方法，以及一个较复杂的案例

```java
// 默认非公平锁，参数传true 表示未公平锁
ReentrantLock lock = new ReentrantLock(false);
// 尝试获取锁
lock()
// 释放锁 应放在finally块中 必须执行到
unlock()
try {
    // 获取锁时可被打断,阻塞中的线程可被打断
    LOCK.lockInterruptibly();
} catch (InterruptedException e) {
    return;
}
// 尝试获取锁 获取不到就返回false
LOCK.tryLock()
// 支持超时时间 一段时间没获取到就返回false
tryLock(long timeout, TimeUnit unit)
// 指定条件变量 休息室 一个锁可以创建多个休息室
Condition waitSet = ROOM.newCondition();
// 释放锁  进入waitSet等待 释放后其他线程可以抢锁
yanWaitSet.await()
// 唤醒具体休息室的线程 唤醒后 重写竞争锁
yanWaitSet.signal()
```

```java
  public static void main(String[] args) {
        AwaitSignal awaitSignal = new AwaitSignal(5);
        // 构建三个条件变量
        Condition a = awaitSignal.newCondition();
        Condition b = awaitSignal.newCondition();
        Condition c = awaitSignal.newCondition();
        // 开启三个线程
        new Thread(() -> {
            awaitSignal.print("a", a, b);
        }).start();

        new Thread(() -> {
            awaitSignal.print("b", b, c);
        }).start();

        new Thread(() -> {
            awaitSignal.print("c", c, a);
        }).start();

        try {
            Thread.sleep(1000);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        awaitSignal.lock();
        try {
            // 先唤醒a
            a.signal();
        } finally {
            awaitSignal.unlock();
        }
    }

}

class AwaitSignal extends ReentrantLock {

    // 循环次数
    private int loopNumber;

    public AwaitSignal(int loopNumber) {
        this.loopNumber = loopNumber;
    }

    /**
     * @param print   输出的字符
     * @param current 当前条件变量
     * @param next    下一个条件变量
     */
    public void print(String print, Condition current, Condition next) {

        for (int i = 0; i < loopNumber; i++) {
            lock();
            try {
                try {
                    // 获取锁之后等待
                    current.await();
                    System.out.print(print);
                } catch (InterruptedException e) {
                    
                }
                next.signal();
            } finally {
                unlock();
            }
        }
    }
```

流程分析：

-  **初始化** ：
  - 主线程创建了 `AwaitSignal` 对象，设置循环次数为 5。
  - 创建了三个 `Condition` 对象：a、b、c，分别对应三个线程。
  - 三个线程启动，分别调用 `print("a", a, b)` 、 `print("b", b, c)` 、 `print("c", c, a)` 。
  - 主线程休眠 1 秒后，获取锁并通过 `a.signal()`  唤醒线程 A。
-  **线程启动后** ：
  - 每个线程进入 `print` 方法，执行 `lock()` 获取锁。由于 `ReentrantLock` 是互斥锁，同一时刻只有一个线程能持有锁。
  - 假设线程 A 先获取锁，它调用 `a.await()` ，释放锁并进入等待状态（等待 `Condition a` 的信号）。
  - 其他线程（B 和 C）尝试 `lock()` ，但锁被占用，它们会阻塞在 `lock()` 上。
-  **主线程唤醒线程A** ：
  - 主线程在 `try { Thread.sleep(1000); }` 后执行 `awaitSignal.lock()` ，获取锁。
  - 调用 `a.signal()` ，唤醒等待在 `Condition a` 上的线程 A。
  - 主线程执行 `unlock()` ，释放锁。
-  **线程A被唤醒后** ：
  - 线程 A 从 `a.await()` 返回，但它需要重新获取锁才能继续执行。
  - 因为主线程已经释放锁（ `unlock()` ），线程 A 成功重新获取锁。
  - 线程 A 打印 "a"，然后调用 `b.signal()` 唤醒线程 B。
  - 线程 A 执行 `unlock()` ，释放锁。
-  **线程B被唤醒后** ：
  - 线程 B 在 `b.await()` 上等待，收到 `b.signal()` 后被唤醒。
  - 线程 B 尝试重新获取锁。由于线程 A 已释放锁，线程 B 获取锁成功。
  - 线程 B 打印 "b"，调用 `c.signal()` 唤醒线程 C，然后释放锁。

#### 小结

`ReentrantLock`可以替代`synchronized`进行同步；

`ReentrantLock`获取锁更安全；

必须先获取到锁，再进入`try {...}`代码块，最后使用`finally`保证释放锁；

可以使用`tryLock()`尝试获取锁。

---



### 线程池

（线程池感觉都写的不是很明白）

Java语言虽然内置了多线程支持，启动一个新线程非常方便，但是，创建线程需要操作系统资源（线程资源，栈空间等），频繁创建和销毁大量线程需要消耗大量时间。

如果可以复用一组线程：

```
┌─────┐ execute  ┌──────────────────┐
│Task1│─────────▶│ThreadPool        │
├─────┤          │┌───────┐┌───────┐│
│Task2│          ││Thread1││Thread2││
├─────┤          │└───────┘└───────┘│
│Task3│          │┌───────┐┌───────┐│
├─────┤          ││Thread3││Thread4││
│Task4│          │└───────┘└───────┘│
├─────┤          └──────────────────┘
│Task5│
├─────┤
│Task6│
└─────┘
  ...
```

那么我们就可以把很多小任务让一组线程来执行，而不是一个任务对应一个新线程。这种能接收大量小任务并进行分发处理的就是线程池。

简单地说，线程池内部维护了若干个线程，没有任务的时候，这些线程都处于等待状态。如果有新任务，就分配一个空闲线程执行。如果所有线程都处于忙碌状态，新任务要么放入队列等待，要么增加一个新线程进行处理。

Java标准库提供了`ExecutorService`接口表示线程池，它的典型用法如下：

```java
// 创建固定大小的线程池:
ExecutorService executor = Executors.newFixedThreadPool(3);
// 提交任务:
executor.submit(task1);
executor.submit(task2);
executor.submit(task3);
executor.submit(task4);
executor.submit(task5);
```

因为`ExecutorService`只是接口，Java标准库提供的几个常用实现类有：

- FixedThreadPool：线程数固定的线程池；
- CachedThreadPool：线程数根据任务动态调整的线程池；
- SingleThreadExecutor：仅单线程执行的线程池。



创建这些线程池的方法都被封装到`Executors`这个类中。我们以`FixedThreadPool`为例，看看线程池的执行逻辑：

```java
// thread-pool
import java.util.concurrent.*;

public class Main {
    public static void main(String[] args) {
        // 创建一个固定大小的线程池:
        ExecutorService es = Executors.newFixedThreadPool(4);
        for (int i = 0; i < 6; i++) {
            es.submit(new Task("" + i));
        }
        // 关闭线程池:
        es.shutdown();
    }
}

class Task implements Runnable {
    private final String name;

    public Task(String name) {
        this.name = name;
    }

    @Override
    public void run() {
        System.out.println("start task " + name);
        try {
            Thread.sleep(1000);
        } catch (InterruptedException e) {
        }
        System.out.println("end task " + name);
    }
}
```

我们观察执行结果，一次性放入6个任务，由于线程池只有固定的4个线程，因此，前4个任务会同时执行，等到有线程空闲后，才会执行后面的两个任务。

线程池在程序结束的时候要关闭。使用`shutdown()`方法关闭线程池的时候，它会等待正在执行的任务先完成，然后再关闭。`shutdownNow()`会立刻停止正在执行的任务，`awaitTermination()`则会等待指定的时间让线程池关闭。

如果我们把线程池改为`CachedThreadPool`，由于这个线程池的实现会根据任务数量动态调整线程池的大小，所以6个任务可一次性全部同时执行。

如果我们想把线程池的大小限制在4～10个之间动态调整怎么办？我们查看`Executors.newCachedThreadPool()`方法的源码：

```java
public static ExecutorService newCachedThreadPool() {
    return new ThreadPoolExecutor(
            0, Integer.MAX_VALUE,
            60L, TimeUnit.SECONDS,
            new SynchronousQueue<Runnable>());
}
```

因此，想创建指定动态范围的线程池，可以这么写：

```java
int min = 4;
int max = 10;
ExecutorService es = new ThreadPoolExecutor(
        min, max,
        60L, TimeUnit.SECONDS,
        new SynchronousQueue<Runnable>());
```



#### ScheduledThreadPool

还有一种任务，需要定期反复执行，例如，每秒刷新证券价格。这种任务本身固定，需要反复执行的，可以使用`ScheduledThreadPool`。放入`ScheduledThreadPool`的任务可以定期反复执行。

创建一个`ScheduledThreadPool`仍然是通过`Executors`类：

```java
ScheduledExecutorService ses = Executors.newScheduledThreadPool(4);
```

我们可以提交一次性任务，它会在指定延迟后只执行一次：

```java
// 1秒后执行一次性任务:
ses.schedule(new Task("one-time"), 1, TimeUnit.SECONDS);
```

如果任务以固定的每3秒执行，我们可以这样写：

```java
// 2秒后开始执行定时任务，每3秒执行:
ses.scheduleAtFixedRate(new Task("fixed-rate"), 2, 3, TimeUnit.SECONDS);
```

如果任务以固定的3秒为间隔执行，我们可以这样写：

```java
// 2秒后开始执行定时任务，以3秒为间隔执行:
ses.scheduleWithFixedDelay(new Task("fixed-delay"), 2, 3, TimeUnit.SECONDS);
```

注意FixedRate和FixedDelay的区别。FixedRate是指任务总是以固定时间间隔触发，不管任务执行多长时间：

```
│░░░░   │░░░░░░ │░░░    │░░░░░  │░░░  
├───────┼───────┼───────┼───────┼────▶
│◀─────▶│◀─────▶│◀─────▶│◀─────▶│
```

而FixedDelay是指，上一次任务执行完毕后，等待固定的时间间隔，再执行下一次任务：

```
│░░░│       │░░░░░│       │░░│       │░
└───┼───────┼─────┼───────┼──┼───────┼──▶
    │◀─────▶│     │◀─────▶│  │◀─────▶│
```

因此，使用`ScheduledThreadPool`时，我们要根据需要选择执行一次、FixedRate执行还是FixedDelay执行。

细心的童鞋还可以思考下面的问题：

- 在FixedRate模式下，假设每秒触发，如果某次任务执行时间超过1秒，后续任务会不会并发执行？
- 如果任务抛出了异常，后续任务是否继续执行？

Java标准库还提供了一个`java.util.Timer`类，这个类也可以定期执行任务，但是，一个`Timer`会对应一个`Thread`，所以，一个`Timer`只能定期执行一个任务，多个定时任务必须启动多个`Timer`，而一个`ScheduledThreadPool`就可以调度多个定时任务，所以，我们完全可以用`ScheduledThreadPool`取代旧的`Timer`。



#### 小结

JDK提供了`ExecutorService`实现了线程池功能：

- 线程池内部维护一组线程，可以高效执行大量小任务；
- `Executors`提供了静态方法创建不同类型的`ExecutorService`；
- 必须调用`shutdown()`关闭`ExecutorService`；
- `ScheduledThreadPool`可以定期调度多个任务。

---

