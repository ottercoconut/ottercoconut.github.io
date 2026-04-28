+++

title = "读懂 Python asyncio：协程与任务"
date = 2026-04-23T16:08:00+08:00
translationKey = "python-async"
tags = ["Python", "asyncio"]
categories = ["后端开发"]

[params]
toc = false

+++

# 读懂 Python asyncio：协程与任务

> 本文基于 *Python 3.11* 的asyncio ，可能会缺失最新版本的特性

asyncio 是用来编写 **并发** 代码的库，使用 `async`/`await` 语法。其被用作多个提供高性能 Python 异步框架的基础，包括网络和网站服务，数据库连接库，分布式任务队列等等。也往往是构建 IO 密集型和高层级 **结构化** 网络代码的最佳选择。

`asyncio` 提供一组 **高层级** API 用于:

- 并发地 [运行 Python 协程](https://docs.python.org/zh-cn/3.11/library/asyncio-task.html#coroutine) 并对其执行过程实现完全控制;
- 执行 [网络 IO 和 IPC](https://docs.python.org/zh-cn/3.11/library/asyncio-stream.html#asyncio-streams);
- 控制 [子进程](https://docs.python.org/zh-cn/3.11/library/asyncio-subprocess.html#asyncio-subprocess);
- 通过 [队列](https://docs.python.org/zh-cn/3.11/library/asyncio-queue.html#asyncio-queues) 实现分布式任务;
- [同步](https://docs.python.org/zh-cn/3.11/library/asyncio-sync.html#asyncio-sync) 并发代码;

## 参考网站

[协程与任务 — Python 3.11.15 文档](https://docs.python.org/zh-cn/3.11/library/asyncio-task.html)

[Python asyncio 模块 | 菜鸟教程](https://www.runoob.com/python3/python-asyncio.html)

[协程 - Python教程 - 廖雪峰的官方网站](https://liaoxuefeng.com/books/python/async-io/coroutine/index.html)


## 协程

源码：[cpython/Lib/asyncio/coroutines.py at 3.11](https://github.com/python/cpython/blob/3.11/Lib/asyncio/coroutines.py)

通过 `async`/`await` 语法来声明协程是编写 asyncio 应用的推荐方式。 例如，以下代码段会打印 "hello"，等待 1 秒，再打印 "world"：

```python
>>> import asyncio
>>> async def main():
...    print('hello')
...    await asyncio.sleep(1)
...    print('world')

>>> asyncio.run(main())
hello
world
```

注意：简单地调用一个协程并不会使其被调度执行：

```python
>>> main()

<coroutine object main at 0x1053bb7c8>
```

要实际运行一个协程，asyncio 提供了以下几种机制:

- [`asyncio.run()`](https://docs.python.org/zh-cn/3.11/library/asyncio-runner.html#asyncio.run) 函数用来运行最高层级的入口点 "main()" 函数 (参见上面的示例。)

- 对协程执行 await。以下代码段会在等待 1 秒后打印 "hello"，然后 *再次* 等待 2 秒后打印 "world"：

  ```python
  import asyncio
  import time
  
  async def say_after(delay, what):
      await asyncio.sleep(delay)
      print(what)
  
  async def main():
      print(f"started at {time.strftime('%X')}")
  
      await say_after(1, 'hello')
      await say_after(2, 'world')
  
      print(f"finished at {time.strftime('%X')}")
  
  asyncio.run(main())
  ```

  预期输出：

  ```python
  started at 17:13:52
  hello
  world
  finished at 17:13:55
  ```

- [`asyncio.create_task()`](https://docs.python.org/zh-cn/3.11/library/asyncio-task.html#asyncio.create_task) 函数用来并发运行作为 asyncio [`任务`](https://docs.python.org/zh-cn/3.11/library/asyncio-task.html#asyncio.Task) 的多个协程。

  让我们修改以上示例，*并发* 运行两个 `say_after` 协程:

  ```python
  async def main():
      task1 = asyncio.create_task(
          say_after(1, 'hello'))
  
      task2 = asyncio.create_task(
          say_after(2, 'world'))
  
      print(f"started at {time.strftime('%X')}")
  
      # Wait until both tasks are completed (should take
      # around 2 seconds.)
      await task1
      await task2
  
      print(f"finished at {time.strftime('%X')}")
  ```

- [`asyncio.TaskGroup`](https://docs.python.org/zh-cn/3.11/library/asyncio-task.html#asyncio.TaskGroup) 类提供了 [`create_task()`](https://docs.python.org/zh-cn/3.11/library/asyncio-task.html#asyncio.create_task) 的更现代化的替代。 使用此 API，之前的例子将变为：

  ```python
  async def main():
      async with asyncio.TaskGroup() as tg:
          task1 = tg.create_task(
              say_after(1, 'hello'))
  
          task2 = tg.create_task(
              say_after(2, 'world'))
  
          print(f"started at {time.strftime('%X')}")
  
      # The await is implicit when the context manager exits.
  
      print(f"finished at {time.strftime('%X')}")
  ```

  现在看来，`asyncio.create_task()` 和 `asyncio.TaskGroup` 最大的区别在于是否需要手动等待(`await`)，其它的特性详见后文。



## 可等待对象

如果一个对象可以在 [`await`](https://docs.python.org/zh-cn/3.11/reference/expressions.html#await) 语句中使用，那么它就是 **可等待** 对象。许多 asyncio API 都被设计为接受可等待对象。

*可等待* 对象有三种主要类型: **协程**，**任务**和**Future**。

- **协程**

  Python 协程属于 *可等待* 对象，因此可以在其他协程中被等待：

  ```python
  import asyncio
  
  async def nested():
      return 42
  
  async def main():
      # Nothing happens if we just call "nested()".
      # A coroutine object is created but not awaited,
      nested()
  
      print(await nested())  # will print "42".
  
  asyncio.run(main())
  ```

  > 在本文档中 "协程" 可用来表示两个紧密关联的概念:
  >
  > - *协程函数*: 定义形式为 [`async def`](https://docs.python.org/zh-cn/3.11/reference/compound_stmts.html#async-def) 的函数;
  > - *协程对象*: 调用 *协程函数* 所返回的对象。

- **任务**

  *任务* 被用来“并行的”调度协程

  当一个协程通过 [`asyncio.create_task()`](https://docs.python.org/zh-cn/3.11/library/asyncio-task.html#asyncio.create_task) 等函数被封装为一个 *任务*，该协程会被自动调度执行：

  ```python
  import asyncio
  
  async def nested():
      return 42
  
  async def main():
      # Schedule nested() to run soon concurrently
      # with "main()".
      task = asyncio.create_task(nested())
  
      # "task" can now be used to cancel "nested()", or
      # can simply be awaited to wait until it is complete:
      await task
  
  asyncio.run(main())
  ```

  当用 `create_task()` 把一个协程包装成任务后，中途不想让这个任务继续执行了，就可以 `task.cancel()` 将其中止，它会在 `nested()` 下一次遇到 `await` 时，注入一个 `asyncio.CancelledError` 异常，详见[任务取消](#任务取消)节。

  当 `task = asyncio.create_task(nested())` 执行后，`nested()` 自动开始运行，如果不写 `await task` ，`main()`通常结束得更快，导致 `nested()` 尚未运行完，协程就已经结束了。

  由于其重要性，详细用法见[Task对象](https://docs.python.org/zh-cn/3.11/library/asyncio-task.html#id15)。

- **Futures**

  [`Future`](https://docs.python.org/zh-cn/3.11/library/asyncio-future.html#asyncio.Future) 是一种特殊的 **低层级** 可等待对象，表示一个异步操作的 **最终结果**。

  当一个 Future 对象 *被等待*，这意味着协程将保持等待直到该 Future 对象在其他地方操作完毕。

  在 asyncio 中需要 Future 对象以便允许通过 async/await 使用基于回调的代码。

  通常情况下 **没有必要** 在应用层级的代码中创建 Future 对象。

  Future 对象有时会由库和某些 asyncio API 暴露给用户，用作可等待对象：

  ```python
  async def main():
      await function_that_returns_a_future_object()
  
      # this is also valid:
      await asyncio.gather(
          function_that_returns_a_future_object(),
          some_python_coroutine()
      )
  ```

  一个很好的返回对象的低层级函数的示例是 [`loop.run_in_executor()`](https://docs.python.org/zh-cn/3.11/library/asyncio-eventloop.html#asyncio.loop.run_in_executor)。



## 休眠

`coroutine asyncio.sleep(delay, result=None)`

阻塞 *delay* 指定的秒数。

如果指定了 *result*，则当协程完成时将其返回给调用者。

`sleep()` 总是会**挂起**当前任务，以允许其他任务运行。

将 delay 设为 0 将提供一个经优化的路径以允许其他任务运行。 这可**供长期间运行的函数使用**以避免在函数调用的全过程中阻塞事件循环。

比如调用 `await asyncio.sleep(0)` 时：

1. **当前任务挂起：** 你的函数暂时停止执行，保存当前的寄存器和栈状态。
2. **排到队尾：** 该任务并没有被放进“等待计时器”的名单，而是直接被放回了 Ready Queue 的末尾。
3. **循环轮转：** 事件循环从 Ready Queue 的**头部**取出下一个任务开始运行。

以下协程示例运行 5 秒，每秒显示一次当前日期：

```python
import asyncio
import datetime

async def display_date():
    loop = asyncio.get_running_loop()
    end_time = loop.time() + 5.0
    while True:
        print(datetime.datetime.now())
        if (loop.time() + 1.0) >= end_time:
            break
        await asyncio.sleep(1)

asyncio.run(display_date())
```



## 创建任务

源码：[cpython/Lib/asyncio/tasks.py at 3.11](https://github.com/python/cpython/blob/3.11/Lib/asyncio/tasks.py)

`asyncio.create_task(coro, *, name=None, context=None)`

将 *coro* [协程](https://docs.python.org/zh-cn/3.11/library/asyncio-task.html#coroutine) 封装为一个 [`Task`](https://docs.python.org/zh-cn/3.11/library/asyncio-task.html#asyncio.Task) 并调度其执行。返回 Task 对象。

*name* 不为 `None`，它将使用 [`Task.set_name()`](https://docs.python.org/zh-cn/3.11/library/asyncio-task.html#asyncio.Task.set_name) 来设为任务的名称。

可选的 *context* 参数允许指定自定义的 [`contextvars.Context`](https://docs.python.org/zh-cn/3.11/library/contextvars.html#contextvars.Context) 供 *coro* 运行。 当未提供 *context* 时将创建当前上下文的副本。

该任务会在 [`get_running_loop()`](https://docs.python.org/zh-cn/3.11/library/asyncio-eventloop.html#asyncio.get_running_loop) 返回的循环中执行，如果当前线程没有在运行的循环则会引发 [`RuntimeError`](https://docs.python.org/zh-cn/3.11/library/exceptions.html#RuntimeError)。

> 保存一个指向此函数的结果的引用，以避免任务在执行过程中消失。 事件循环将只保留对任务的弱引用。 未在其他地方被引用的任务可能在任何时候被作为垃圾回收，即使是在它被完成之前。 如果需要可靠的“发射后不用管”后台任务，请将它们放到一个多项集中：
>
> ```python
> background_tasks = set()
> 
> for i in range(10):
>     task = asyncio.create_task(some_coro(param=i))
> 
>     # Add task to the set. This creates a strong reference.
>     background_tasks.add(task)
> 
>     # To prevent keeping references to finished tasks forever,
>     # make each task remove its own reference from the set after
>     # completion:
>     task.add_done_callback(background_tasks.discard)
> ```

这段文档触及了Python的“事件循环”和“垃圾回收”机制，下面简单解释一下，具体的学习可能会单独写篇文章：

### 事件循环

为什么 `asyncio` 的事件循环（Event Loop）只对 Task 对象保留弱引用 `weakref` ？这是出于**防止内存泄漏的防御性设计**。

事件循环是一个长期运行的底层死循环（通常伴随整个进程的生命周期）。如果事件循环内部维护一个强引用列表来追踪所有被 `create_task()` 启动的后台任务：

1. 那些执行完毕或被取消的任务，必须由事件循环主动去清理它们。
2. 如果清理机制存在任何延迟或缺陷，或者开发者创建了海量的“发射后不管”任务，事件循环的内部列表会无限膨胀，最终导致内存溢出 (OOM)。

因此，`asyncio` 制定了明确的契约：**事件循环只负责“调度”协程，不负责“维持” Task 对象的生命周期。** 维持 Task 生命周期的责任被完全移交给了调用方（开发者）。事件循环通过弱引用来追踪任务状态，一旦调用方丢失了对 Task 的强引用，事件循环不会阻止该 Task 被销毁。

### 垃圾回收

Python 会在底层追踪每一个内存对象被引用了多少次。根据引用状态的不同，GC (Garbage Collection) 的处理逻辑如下：

- **处理强引用对象**

  当你将一个对象赋值给一个变量（如 `a = MyObject()`），或者将其加入到列表、字典等数据结构中时，就创建了一个强引用。那么该对象的内部属性“引用计数”会加 1。

  只要一个对象的引用计数**大于 0**，垃圾回收机制就会判定该对象正在被使用。GC 会完全忽略它，确保其在内存中安全存活。

- **处理非强引用对象**

  当变量的作用域结束、变量被重新赋值，或者使用 `del` 显式删除变量时，原对象的强引用就会解除。此外，使用 `weakref` 模块创建的“弱引用”也属于非强引用。强引用的解除会导致对象的引用计数减 1。弱引用虽然指向该对象，但**不会**增加对象的引用计数。

  一旦对象的强引用计数**降为 0**：

  1. GC 会**立即**介入，调用该对象的析构方法（`__del__`）。
  2. 立即释放该对象占用的内存空间。
  3. 所有指向该对象的弱引用会自动失效（返回值变为 `None`）。

  > 如果两个对象互相强引用对方，导致计数永远不为 0，Python 的辅助机制“分代回收器”会定期扫描并销毁这种无法被外部访问的孤立对象簇。

### 上下文变量

`create_task()` 的 `context` 参数是用来解决异步并发下**“数据隔离与传递”**的。默认（多数）情况下它会自动复印当前状态，保证子任务能拿到父任务的上下文数据；如果想阻断这种继承，就可以手动传一个自定义的 `context` 进去。

还需注意，上下文变量并不是在协程内部创建，而一般是在全局创建。下面只做一个简单示例，更复杂的内容（比如子协程临时修改上下文变量）可能要单独写篇文章：

```python
import asyncio
import contextvars

# 1. 【全局】创建一个名为 'user_id' 的上下文变量（类似一把钥匙
# 这把钥匙是专门用来存储和检索当前任务相关的数据的）
user_id_var = contextvars.ContextVar('user_id')

async def write_log(action):
    # 3. 【底层函数】获取当前任务对应的 'user_id'（每个任务都有自己独立的“背包”）
    # 张三的任务获取的是张三，李四的任务获取的是李四
    current_user = user_id_var.get()
    print(f"[{current_user}] 执行了操作: {action}")

async def handle_request(name):
    # 2. 【顶层入口】设置当前任务的 'user_id'（将数据放入当前任务的“背包”）
    # 这里我们把用户名称（如张三或李四）赋值给当前任务的上下文变量
    user_id_var.set(name)
    
    # 模拟复杂的操作过程，任务间不需要传递数据！直接使用上下文变量。
    await write_log("登录系统")
    await asyncio.sleep(1)  # 模拟任务的并发执行，控制权被交出
    await write_log("退出系统")

async def main():
    # 并发执行两个请求任务，确保每个任务独立，不会互相干扰
    # 即使任务交替执行，上下文数据（如 'user_id'）也会保持准确
    await asyncio.gather(
        handle_request("张三"),
        handle_request("李四")
    )

# 运行主程序，启动异步任务
asyncio.run(main())

# 输出结果（交替打印，但每个任务的输出始终正确，保持隔离）：
# [张三] 执行了操作: 登录系统
# [李四] 执行了操作: 登录系统
# [张三] 执行了操作: 退出系统
# [李四] 执行了操作: 退出系统
```



## 并发运行任务

当多个协程之间没有依赖关系时，我们通常不希望它们一个接一个执行，而是希望它们同时开始，谁需要等待 I/O，谁就把控制权交还给事件循环，让其他任务继续运行。

`asyncio.gather()` 就适合这种场景：**并发运行一组可等待对象，并在它们全部完成后，一次性拿到结果。**

比如下面这个例子中，`factorial("A", 2)`、`factorial("B", 3)` 和 `factorial("C", 4)` 彼此之间没有依赖，因此可以并发执行：

```python
import asyncio

async def factorial(name, number):
    f = 1
    for i in range(2, number + 1):
        print(f"Task {name}: Compute factorial({number}), currently i={i}...")
        await asyncio.sleep(1)
        f *= i
    print(f"Task {name}: factorial({number}) = {f}")
    return f

async def main():
    L = await asyncio.gather(
        factorial("A", 2),
        factorial("B", 3),
        factorial("C", 4),
    )
    print(L)

asyncio.run(main())
```

运行结果大致如下：

```python
Task A: Compute factorial(2), currently i=2...
Task B: Compute factorial(3), currently i=2...
Task C: Compute factorial(4), currently i=2...
Task A: factorial(2) = 2
Task B: Compute factorial(3), currently i=3...
Task C: Compute factorial(4), currently i=3...
Task B: factorial(3) = 6
Task C: Compute factorial(4), currently i=4...
Task C: factorial(4) = 24
[2, 6, 24]
```

这里最值得注意的是：虽然三个任务的打印顺序是交错的，但 `gather()` 返回结果的顺序仍然和传入顺序一致。

也就是说：

```python
L = await asyncio.gather(
    factorial("A", 2),
    factorial("B", 3),
    factorial("C", 4),
)
```

最终得到的是：

```python
[2, 6, 24]
```

而不是按照哪个任务先完成来排序。

`gather()` 有几个常用规则：

1. 如果传入的是协程对象，它会自动被包装成任务并调度执行。
2. 如果所有可等待对象都成功完成，返回值是一个列表。
3. 返回列表的顺序和传入顺序一致。
4. 如果 `gather()` 本身被取消，所有尚未完成的任务也会被取消。

比较容易忽略的是异常处理。

默认情况下，如果其中某个任务抛出异常，异常会传播给正在 `await gather()` 的地方。但这并不意味着其他任务一定会立刻停止。对于已经提交给 `gather()` 的其他可等待对象，它们不会因为其中一个任务抛错就自动取消，而是会继续运行。

如果你希望把异常也当作结果收集起来，可以使用 `return_exceptions=True`：

```python
results = await asyncio.gather(
    factorial("A", 2),
    factorial("B", 3),
    factorial("C", 4),
    return_exceptions=True,
)
```

这样异常会作为列表中的一个元素返回，调用方需要自己判断哪些结果是正常值，哪些是异常。

因此，我对 `gather()` 的理解是：它更像是一个“结果收集器”。当你关心的是“一组任务都跑完之后，各自返回了什么”时，它很合适。

但如果你更关心的是“一组任务属于同一个生命周期，其中一个失败时其他任务也应该被取消”，那么 Python 3.11 之后更推荐使用 `TaskGroup`。这也是下一节要讨论的内容。



## 任务组

任务组合并了一套用于等待分组中所有任务完成的方便可靠方式的任务创建 API。

`class asyncio.TaskGroup` : 持有一个任务分组的 [异步上下文管理器](https://docs.python.org/zh-cn/3.11/reference/datamodel.html#async-context-managers)。 可以使用 [`create_task()`](https://docs.python.org/zh-cn/3.11/library/asyncio-task.html#asyncio.create_task) 将任务添加到分组中。 当该上下文管理器退出时所有任务都将被等待。

`TaskGroup.create_task(coro, *, name=None, context=None)` : 在该任务组中创建一个任务。 其签名与 [`asyncio.create_task()`](https://docs.python.org/zh-cn/3.11/library/asyncio-task.html#asyncio.create_task) 的相匹配。

示例：

```python
async def main():
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(some_coro(...))
        task2 = tg.create_task(another_coro(...))
    print("Both tasks have completed now.")
```

`async with` 语句将等待分组中的所有任务结束。 在等待期间，仍可将新任务添加到分组中 (例如，通过将 `tg` 传入某个协程并在该协程中调用 `tg.create_task()`)。 一旦最后的任务完成并退出 `async with` 代码块，将无法再向分组添加新任务。

关于其异常处理，文档写的过于繁琐了，总结如下： 

-  如果任务因非 `asyncio.CancelledError` 异常失败，其他任务会被取消，且无法再添加任务。 
-  失败的异常会被包装成 `ExceptionGroup` 或 `BaseExceptionGroup`，统一抛出。 
-  如果任务失败时是 `KeyboardInterrupt` 或 `SystemExit`，它们会优先被抛出，而不会归入异常组。 

如果发生取消与等待： 

-  如果 `async with` 语句因异常退出，剩余任务会被取消并等待完成。 
-  异常（除了 `CancelledError`）会被加入异常组，最终一起抛出。

### 异步上下文管理器

上面说 `TaskGroup` 是一个异步上下文管理器，关键就在这一句：

```python
async with asyncio.TaskGroup() as tg:
    ...
```

它看起来只是普通的代码块，但实际上 Python 会在进入代码块之前调用 `__aenter__()`，在离开代码块时调用 `__aexit__()`。异步上下文管理器和普通上下文管理器的区别是：这两个方法的结果都要被 `await`。

可以把 `async with` 粗略理解成下面的展开形式：

```python
manager = asyncio.TaskGroup()
tg = await manager.__aenter__()

try:
    ...
except BaseException as exc:
    suppress = await manager.__aexit__(type(exc), exc, exc.__traceback__)
    if not suppress:
        raise
else:
    await manager.__aexit__(None, None, None)
```

这段伪代码里有两个重点。

第一个重点是：`__aenter__()` 决定进入代码块时要准备什么，以及 `as tg` 拿到什么。对 `TaskGroup` 来说，`__aenter__()` 会让这个任务组进入可用状态，并把任务组对象本身返回给 `tg`，所以后面才能调用 `tg.create_task()`。

第二个重点是：`__aexit__()` 决定离开代码块时要收尾什么。对 `TaskGroup` 来说，真正重要的逻辑就在这里：它会等待组里的任务结束；如果有任务失败，它会取消其他任务；最后再把异常整理后抛出。

这里容易混淆 `__aexit__()` 和 `__await__()`。`async with` 协议本身调用的是 `__aenter__()` 和 `__aexit__()`，不是直接调用 `__await__()`。但由于这两个方法必须返回可等待对象，所以 Python 在执行：

```python
await manager.__aexit__(None, None, None)
```

时，会走普通 `await` 表达式的逻辑。对于 `async def __aexit__(...)` 来说，调用它会得到一个协程对象；这个协程对象本身是可等待对象，底层通过它的 `__await__()` 交给事件循环驱动执行。

换句话说，可以这样理解这几层关系：

```text
async with
  -> 调用 __aenter__ / __aexit__
  -> await 它们返回的可等待对象
  -> 可等待对象通过 __await__ 被事件循环推进
```

所以 `TaskGroup` 能在退出代码块时“自动等待所有任务”，并不是因为 `async with` 天生懂任务组，而是因为 `TaskGroup.__aexit__()` 把等待、取消和异常整理这些逻辑都写在了退出阶段。

#### `__aexit__()`

当离开 `async with` 代码块（或者代码块内部发生了错误）时，Python 会自动调用 `TaskGroup` 的 `__aexit__(self, exc_type, exc_value, traceback)`。

它也实现了处理 `TaskGroup` 中遇到异常等情况的逻辑：

1. **等待所有任务**：代码块里的语句执行完，并不代表任务组里的任务都结束了。`__aexit__()` 会在这里等待组里所有任务完成。
2. **接收代码块异常**：如果 `async with` 内部本身抛出了异常，`exc_type, exc_value, traceback` 会把这个异常传进 `__aexit__()`。
3. **处理子任务异常**：如果某个子任务抛出了非 `CancelledError` 异常，`TaskGroup` 会取消其他还在运行的任务。
4. **整理异常并抛出**：多个异常会被收集进 `ExceptionGroup` 或 `BaseExceptionGroup`，再统一抛给外层代码。

这也解释了为什么 `TaskGroup` 比裸用 `create_task()` 更“结构化”：任务不是散落在事件循环里各跑各的，而是被一个退出阶段统一收束。

## 任务取消

任务可以便捷和安全地取消。 当任务被取消时，[`asyncio.CancelledError`](https://docs.python.org/zh-cn/3.11/library/asyncio-exceptions.html#asyncio.CancelledError) 将在遇到机会时在任务中被引发。

推荐协程使用 `try/finally` 代码块来可靠地执行清理逻辑。 对于 [`asyncio.CancelledError`](https://docs.python.org/zh-cn/3.11/library/asyncio-exceptions.html#asyncio.CancelledError) 被显式捕获的情况，它通常应当在清理完成时被传播。 [`asyncio.CancelledError`](https://docs.python.org/zh-cn/3.11/library/asyncio-exceptions.html#asyncio.CancelledError) 会直接子类化 [`BaseException`](https://docs.python.org/zh-cn/3.11/library/exceptions.html#BaseException) 因此大多数代码都不需要关心这一点。

启用结构化并发的 asyncio 组件，如 [`asyncio.TaskGroup`](https://docs.python.org/zh-cn/3.11/library/asyncio-task.html#asyncio.TaskGroup) 和 [`asyncio.timeout()`](https://docs.python.org/zh-cn/3.11/library/asyncio-task.html#asyncio.timeout)，在内部是使用撤销操作来实现的因而在协程屏蔽了 [`asyncio.CancelledError`](https://docs.python.org/zh-cn/3.11/library/asyncio-exceptions.html#asyncio.CancelledError) 时可能无法正常工作。 类似地，用户代码通常也不应调用 [`uncancel`](https://docs.python.org/zh-cn/3.11/library/asyncio-task.html#asyncio.Task.uncancel)。 但是，在确实想要屏蔽 [`asyncio.CancelledError`](https://docs.python.org/zh-cn/3.11/library/asyncio-exceptions.html#asyncio.CancelledError) 的情况下，则还有必要调用 `uncancel()` 来完全移除撤销状态。



## 超时

异步程序里，超时不是锦上添花，而是很重要的防御措施。

比如请求接口、读取文件、等待某个远端服务响应时，如果没有超时限制，一个任务可能会一直挂在那里。它未必占用 CPU，但会占住连接、内存、任务槽位等资源，也会让上层逻辑迟迟拿不到结果。

在 Python 3.11 里，我更倾向优先使用 `asyncio.timeout()`。它是一个异步上下文管理器，适合给“一段异步代码”设置时间限制：

```python
async def main():
    try:
        async with asyncio.timeout(10):
            await long_running_task()
    except TimeoutError:
        print("The long operation timed out, but we've handled it.")

    print("This statement will run regardless.")
```

这里最容易写错的地方是：`TimeoutError` 要在 `async with` 外面捕获。

原因是 `asyncio.timeout()` 的内部机制大致是：

1. 时间到了，取消当前任务。
2. 当前任务中会出现 `asyncio.CancelledError`。
3. `timeout()` 在退出上下文管理器时把它转换成 `TimeoutError`。

所以在 `async with` 代码块里面捕获 `TimeoutError` 是捕获不到的，因为转换发生在上下文退出时。

如果超时时间一开始还不能确定，可以先传入 `None`，之后再通过 `reschedule()` 调整。更精确地指定结束时间点时，也可以使用 `asyncio.timeout_at()`。这些属于更细的控制，日常使用里先掌握 `asyncio.timeout()` 就够了。

另一个常见 API 是 `asyncio.wait_for()`。它更适合给“单个可等待对象”设置超时：

```python
async def eternity():
    await asyncio.sleep(3600)
    print('yay!')

async def main():
    try:
        await asyncio.wait_for(eternity(), timeout=1.0)
    except TimeoutError:
        print('timeout!')

asyncio.run(main())

# Expected output:
#
#     timeout!
```

`wait_for()` 超时后也会取消传入的任务，并引发 `TimeoutError`。需要注意的是，它会等待底层任务确实完成取消流程，所以实际等待时间可能略微超过设置的 `timeout`。

简单来说：

| 场景 | 推荐写法 |
| :-- | :-- |
| 给一段异步代码加超时 | `asyncio.timeout()` |
| 给单个 awaitable 加超时 | `asyncio.wait_for()` |
| 不希望被超时取消影响内部任务 | 配合 `asyncio.shield()` |

不过最后一种情况要谨慎使用，因为“外层不等了，但内层任务还在跑”会让任务生命周期变得更难管理。

## 屏蔽取消操作

`awaitable asyncio.shield(aw)`

保护一个 [可等待对象](https://docs.python.org/zh-cn/3.11/library/asyncio-task.html#asyncio-awaitables) 防止其被 [`取消`](https://docs.python.org/zh-cn/3.11/library/asyncio-task.html#asyncio.Task.cancel)。

如果 *aw* 是一个协程，它将自动被作为任务调度。

以下语句:

```python
task = asyncio.create_task(something())
res = await shield(task)
```

相当于:

```python
res = await something()
```

*不同之处* 在于如果包含它的协程被取消，在 `something()` 中运行的任务不会被取消。从 `something()` 的角度看来，取消操作并没有发生。然而其调用者已被取消，因此 "await" 表达式仍然会引发 [`CancelledError`](https://docs.python.org/zh-cn/3.11/library/asyncio-exceptions.html#asyncio.CancelledError)。

如果通过其他方式取消 `something()` (例如在其内部操作) 则 `shield()` 也会取消。

如果希望完全忽略取消操作 (不推荐) 则 `shield()` 函数需要配合一个 try/except 代码段，如下所示：

```python
task = asyncio.create_task(something())
try:
    res = await shield(task)
except CancelledError:
    res = None
```

> 重要：保存一个传给此函数的任务的引用，以避免任务在执行过程中消失。事件循环将只保留对任务的弱引用。未在其他地方被引用的任务可能在任何时候被作为垃圾回收，即使是在它被完成之前。



## 简单等待

`coroutine asyncio.wait(aws, *, timeout=None, return_when=ALL_COMPLETED)`

并发地运行 *aws* 可迭代对象中的 [`Future`](https://docs.python.org/zh-cn/3.11/library/asyncio-future.html#asyncio.Future) 和 [`Task`](https://docs.python.org/zh-cn/3.11/library/asyncio-task.html#asyncio.Task) 实例并进入阻塞状态直到满足 *return_when* 所指定的条件。

可迭代对象 *aws* 不能为空并且不接受产生任务的生成器。

返回两个 Task/Future 集合: `(done, pending)`。

用法：

```python
done, pending = await asyncio.wait(aws)
```

如指定 *timeout* (float 或 int 类型) 则它将被用于控制返回之前等待的最长秒数。

请注意此函数不会引发 [`TimeoutError`](https://docs.python.org/zh-cn/3.11/library/exceptions.html#TimeoutError)。 当超时发生时尚未完成的 Future 或 Task 会在设定的秒数后被直接返回。

*return_when* 指定此函数应在何时返回。它必须为以下常数之一:

| 常量                        | 描述                                                         |
| :-------------------------- | :----------------------------------------------------------- |
| asyncio.**FIRST_COMPLETED** | 函数将在任意可等待对象结束或取消时返回。                     |
| asyncio.**FIRST_EXCEPTION** | 该函数将在任何 future 对象通过引发异常而结束时返回。 如果没有任何 future 对象引发引发那么它将等价于 [`ALL_COMPLETED`](https://docs.python.org/zh-cn/3.11/library/asyncio-task.html#asyncio.ALL_COMPLETED)。 |
| asyncio.**ALL_COMPLETED**   | 函数将在所有可等待对象结束或取消时返回。                     |



`asyncio.as_completed(aws, *, timeout=None)`

并发地运行可迭代对象 *aws* 中的 [可等待对象](https://docs.python.org/zh-cn/3.11/library/asyncio-task.html#asyncio-awaitables)。 产生任务的生成器不可被用作 *aws* 可迭代对象。 返回一个产生协程的迭代器。 所返回的每个协程可被等待以便从剩余的可等待对象的可迭代对象中获得早最的下一个结果。

如果在所有 Future 对象完成之前发生超时则将引发 [`TimeoutError`](https://docs.python.org/zh-cn/3.11/library/exceptions.html#TimeoutError)。

示例:

```python
for coro in as_completed(aws):
    earliest_result = await coro
    # ...
```

## 在线程中运行

`asyncio.to_thread()` 适合处理一种很常见的尴尬情况：你正在写异步代码，但手里有一个只能同步调用的阻塞函数。

如果直接在协程里调用这个函数，它会卡住事件循环，让其他任务也没法继续运行。`to_thread()` 的作用就是把这个同步函数丢到另一个线程里执行，然后在异步代码里用 `await` 等它的结果。

```python
import asyncio
import time

def read_file_slowly():
    time.sleep(1)
    return "file content"

async def main():
    result = await asyncio.to_thread(read_file_slowly)
    print(result)

asyncio.run(main())
```

它通常用于文件读写、同步数据库驱动、旧 SDK 调用这类 **IO 密集型** 阻塞操作。由于 GIL 的存在，它一般不适合用来加速纯 Python 的 CPU 密集型计算。



## 跨线程调度

`asyncio.run_coroutine_threadsafe()` 用于从另一个线程向某个事件循环提交协程。

这个 API 平时不常用。只有当你的程序里同时存在普通线程和 asyncio 事件循环，并且某个线程需要把协程交给事件循环执行时，才会用到它。

```python
coro = asyncio.sleep(1, result=3)
future = asyncio.run_coroutine_threadsafe(coro, loop)

result = future.result(timeout=2)
```

它返回的是 `concurrent.futures.Future`，不是 `asyncio.Future`。因此获取结果时用的是同步世界里的 `future.result()`。如果等待超时，也可以取消它：

```python
try:
    result = future.result(timeout=2)
except TimeoutError:
    future.cancel()
```

需要注意的是，它要求显式传入事件循环 `loop`，而且应该从事件循环所在之外的线程调用。



## 内省

内省 API 主要用于调试、监控或框架内部逻辑。日常业务代码一般不需要频繁使用。

常见的有三个：

| API | 用途 |
| :-- | :-- |
| `asyncio.current_task()` | 获取当前正在运行的 `Task` |
| `asyncio.all_tasks()` | 获取当前事件循环中尚未完成的所有 `Task` |
| `asyncio.iscoroutine(obj)` | 判断对象是不是协程对象 |

例如调试当前事件循环里还有哪些任务没结束：

```python
for task in asyncio.all_tasks():
    print(task)
```

这些函数适合在排查任务泄漏、定位后台任务状态、编写异步框架时使用。对于普通应用代码来说，知道它们存在即可。

