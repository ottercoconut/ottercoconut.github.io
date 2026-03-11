+++
title = "Redis"
date = 2025-03-18T15:41:00+08:00
translationKey = "redis"
tags = ["缓存", "持久化", "数据库"]
categories = ["技术", "后端开发"]

[params]
toc = true
+++

Redis（Remote Dictionary Server）是一个高性能的开源内存数据结构存储系统，常被用作数据库、缓存和消息代理。

### 参考网站  

[知乎 超强、超详细Redis入门教程](https://zhuanlan.zhihu.com/p/411888708)  

[CSDN【Redis二三事】一套超详细的Redis学习教程（步骤图片+实操）---第一集](https://blog.csdn.net/wenwenaier/article/details/121878831)

> 详细，附有业务场景的实例

## 数据结构  

Redis包含五大数据类型：字符串(``string``), 列表(``list``), 哈希(``hash``), 集合(``set``), 集合(``zset``)  

### string  

Redis 最基本的数据类型，每个键对应一个值，值可以是文本、数字或二进制数据，最大存储 512MB。支持字符串拼接、截取、递增递减等操作，适用于缓存数据、计数器（如访问量统计）、分布式锁等场景。  

#### 基础操作  

```redis
set key value
get key
del key 
```

##### 添加修改多个数据  

```redis
mset key1 value1 key2 value2...
```

##### 获取多个数据  

```redis
mget key1 key2...
```

##### 获取数据的字符个数  

```redis
strlen key
//例如
set name1 nosql
strlen name1
//输出为: 5
```

##### 追加信息  

```redis
append key value
//例如
append name1 name
get name1
/*输出为: nosqlname*/
```

##### 多数据操作与单数据操作  

- 单指令执行 n 条指令需要 n次发送 + n次处理 + n次返回
- 多指令执行 n 条指令需要 1次发送 + n次处理 + 1次返回
- 数据量较大时，多指令消耗的时间远远少于单指令
  
#### 扩展操作  

##### 设置数值数据增加/减少指定范围的值

```redis
incrby key increment
decrby key increment
```

##### 对字符串类型进行数值操作  

```
127.0.0.1:6379> set mynum "2"
OK
127.0.0.1:6379> get mynum
"2"
127.0.0.1:6379> incr mynum
(integer) 3
127.0.0.1:6379> get mynum
"3"
```

遇到数值操作，redis会自动将字符串类型转换成数值  

#### string类型数值操作的注意事项  

- 数据操作不成功的反馈与数据正常操作之间的差异
  - 表示运行结果是否成功
    - （integer）0->false 失败
    - （integer）1->true 成功
  - 表示运行结果值
    - （integer）3->3      3个
    - （integer）1->1      1个
- 数据未获取到
  - （''nil''）等同于''null''
- 数据最大存储量
  - 512MB
- 数值计算最大范围（''java''中的''long''的最大值）
  - 9223372036854775807
  
---

### hash

类似于小型的键值存储，适用于存储结构化数据，如用户信息（ID、姓名、邮箱等），相比 ``String`` 类型更节省内存，因为多个字段共享同一个键。可以对字段进行单独操作，避免整体读取修改，适用于存储对象、会话信息等。  

#### 基础操作  

```redis
hset key field value //添加/修改数据
hget key field //获取数据
hgetall key
hdel key field1 [field2]
```

##### 添加/修改多个数据  

```redis
hmset key field1 value1 field2 value2
```

##### 获取多个数据  

```redis
hmget key field1 field2...
```

##### 获取哈希表中字段的数量

```redis
hlen key
```

##### 获取哈希表中是否存在指定的字段

```redis
hexists key field
```



#### 扩展操作  

##### 获取哈希表中所有字段名或字段值  

```redis
hkeys key
hvals key
```

##### 设置指定字段的数值数据增加指定范围的值

```redis
hincrby key field increment
```

##### 综合示例

```redis
//建立哈希，并赋值
127.0.0.1:6379> HMSET user:001 username antirez password P1pp0 age 34 
OK
//列出哈希的内容
127.0.0.1:6379> HGETALL user:001 
1) "username"
2) "antirez"
3) "password"
4) "P1pp0"
5) "age"
6) "34"
//更改哈希中的某一个值
127.0.0.1:6379> HSET user:001 password 12345 
(integer) 0
//再次列出哈希的内容
127.0.0.1:6379> HGETALL user:001 
1) "username"
2) "antirez"
3) "password"
4) "12345"
5) "age"
6) "34"
```

#### hash类型数据操作的注意事项

- 1.``hash``类型下的``value``**只能存储字符串**，不允许存储其他数据类型，不存在嵌套现象。如果数据未获取到，对应的值为（``nil``）
- 2.每个``hash``可以存储2^23-1个键值对
- 3.``hash``类型十分贴近对象的数据存储形式，并且可以灵活添加对象属性。但hash设计初衷不是为了存储大量对象而设计的，切记不可滥用，**更不可以将hash作为对象列表使用**
- 4.``hgetall``操作可以获取全部属性，如果内部``field``过多，遍历整体数据效率就会很低，有可能成为数据访问瓶颈
---

### list

基于双向链表实现，可以从头部（左侧）或尾部（右侧）快速插入和删除元素，同时支持指定范围的索引读取。适合实现消息队列、时间轴（如微博动态）、任务调度等应用，尤其适用于需要按照插入顺序处理数据的场景。

#### 基础操作  

##### 添加/修改数据

```redis
lpush key value1 [value2]... //从左边进
rpush key value1 [value2]... /*从右边进*/
```

##### 获取数据

关于``lrange``:  

- lrange用来获取指定范围的元素  
- -1 代表倒数第一个元素  
- 列表元素索引从位置0开始  

```redis
lrange key start stop
lindex key index
lien key
```

##### 获取并移除数据

```redis
lpop key
rpop key
```

##### 移除指定数据

关于``lrem``:  

- 参数``count``
  - ``count > 0`` → 从头（左侧）开始删除``count``个匹配的``value``
  - ``count < 0`` → 从尾（右侧）开始删除``count``个匹配的``value``
  - ``count = 0`` → 删除**所有匹配的``value``**（等价于删除列表中所有该值的元素）
- 如果``key``不存在
  - 返回 0
- 常用于**去除列表中的重复元素或清理数据**

```redis
lrem key count value
```



#### 扩展操作  

##### 在规定时间内获取并移除数据  

关于``blpop``:  

- 参数``key1 [key2...]``
  - 可以提供多个列表的键名，``Redis`` 会按照顺序依次检查这些列表
- 参数``timeout``
  - timeout > 0 → 如果列表为空，则最多等待 ``timeout`` 秒
  - timeout < 0 → 永远**阻塞**，直到有数据可用
- 适用于**任务队列、生产者-消费者模型**等场景

```redis
blpop key1 [key2] timeout
brpop key1 [key2] timeout
```

示例  

```redis
RPUSH list1 "a" "b" "c"    // 列表内容：["a", "b", "c"]
BLPOP list1 10             // 取出 "a"，返回 ["list1", "a"]
BLPOP list1 10             // 取出 "b"，返回 ["list1", "b"]
BLPOP list1 10             // 取出 "c"，返回 ["list1", "c"]
BLPOP list1 10             /* 列表为空，阻塞最多 10 秒，若无新元素，则返回 nil */
```

##### 综合示例

```redis
//新建一个list叫做mylist，并在列表头部插入元素"1"
127.0.0.1:6379> lpush mylist "1" 
//返回当前mylist中的元素个数
(integer) 1 
//在mylist右侧插入元素"2"
127.0.0.1:6379> rpush mylist "2" 
(integer) 2
//在mylist左侧插入元素"0"
127.0.0.1:6379> lpush mylist "0" 
(integer) 3
//列出mylist中从编号0到编号1的元素
127.0.0.1:6379> lrange mylist 0 1 
1) "0"
2) "1"
//列出mylist中从编号0到倒数第一个元素
127.0.0.1:6379> lrange mylist 0 -1 
1) "0"
2) "1"
3) "2"
```

#### list类型数据操作注意事项  

- 1.``list``中保存的数据都是``string``类型的，数据总容量是有限的，最多2^32-1个元素  
- 2.``list``具有''索引''的概念，但是操作数据时通常以''队列''的形式进行入队出队操作，或以''栈''的形式进行入栈出栈操作  
- 3.获取全部数据操作结束索引设置为-1  
- 4.``list``可以对数据进行``分页``操作，通常第1页的信息来自于``list``，第2页及更多的信息通过''数据库''的形式加载  

---

### set

由唯一无序的元素组成，支持 O(1) 时间复杂度的添加、删除和查找操作，并提供交集、并集、差集等集合运算，适用于去重、推荐系统中的共同关注、标签管理等应用。由于不允许重复元素，可以高效存储不重复的数据集合。

#### 基础操作

##### 添加数据

```redis
sadd key member1 [member2]
```

##### 获取全部数据

```redis
smembers key
```

##### 删除数据

```redis
srem key member1 [member2]
```

##### 获取集合数据总量

```redis
scard key
```

##### 判断集合中是否包含指定数据

```redis
sismember key member
```

#### 进阶操作

##### 随机获取集合中指定数量的数据

```redis
srandmember key [count]
```

##### 随机获取集合中的某个数据并将其移出集合

```redis
spop key
```

##### 求两个集合的交、并、差集

```redis
sinter key1 [key2]
sunion key1 [key2]
sdiff key1 [key2]
```

##### 求两个集合的交、并、差集 并存储到指定集合中

```redis
sinterstore destination key1 [key2]
sunionstore destination key1 [key2]
sdiffstore destination key1 [key2]
```

##### 将指定数据从原始集合中移动到目标集合中

```redis
smove source destination member
```



##### 综合示例

```redis
//向集合myset中加入一个新元素"one"
127.0.0.1:6379> sadd myset "one" 
(integer) 1
127.0.0.1:6379> sadd myset "two"
(integer) 1
//列出集合myset中的所有元素
127.0.0.1:6379> smembers myset 
1) "one"
2) "two"
//判断元素1是否在集合myset中，返回1表示存在
127.0.0.1:6379> sismember myset "one" 
(integer) 1
//判断元素3是否在集合myset中，返回0表示不存在
127.0.0.1:6379> sismember myset "three" 
(integer) 0
//新建一个新的集合yourset
127.0.0.1:6379> sadd yourset "1" 
(integer) 1
127.0.0.1:6379> sadd yourset "2"
(integer) 1
127.0.0.1:6379> smembers yourset
1) "1"
2) "2"
//对两个集合求并集
127.0.0.1:6379> sunion myset yourset 
1) "1"
2) "one"
3) "2"
4) "two"
```

#### set类型数据操作的注意事项

- set类型`不允许数据重复`，如果添加的数据在set中已经存在，将只`保留一份`
- set虽然和hash的`存储结构相同`，但是`无法启用hash中存储值的空间`



### zset

在 Set 的基础上增加了一个分数（score），并按分数排序，支持范围查询、按分数排名等操作。适用于排行榜（如游戏积分榜）、优先级队列（如定时任务）、时间排序数据存储（如文章阅读量排名）等需要按权重排序的场景。

#### 基础操作

##### 添加数据

```redis
zadd key score1 member1 [score2 member2]
```

##### 获取全部数据

```redis
zrange key start stop [WITHSCORES]     //按从小到大的顺序展示
zrevrange key start stop [WITHSCORES]  //按从大到小的顺序展示
```

##### 删除数据

```redis
zrem key member [member...]
```

##### 按条件获取数据

```redis
zrangebyscore key min max [Withscores][limit]
zrevrangebyscore key max min [withscores]
```

##### 按条件删除数据

```redis
zremrangebyrank key start stop  //按索引删除
zremrangebyscore key min max 	//按范围删除
```

##### 综合示例

```redis
//新增一个有序集合myzset，并加入一个元素baidu.com，给它赋予的序号是1：
127.0.0.1:6379> zadd myzset 1 baidu.com 
(integer) 1
//向myzset中新增一个元素360.com，赋予它的序号是3
127.0.0.1:6379> zadd myzset 3 360.com 
(integer) 1
//向myzset中新增一个元素google.com，赋予它的序号是2
127.0.0.1:6379> zadd myzset 2 google.com 
(integer) 1
//列出myzset的所有元素，同时列出其序号，可以看出myzset已经是有序的了。
127.0.0.1:6379> zrange myzset 0 -1 with scores 
1) "baidu.com"
2) "1"
3) "google.com"
4) "2"
5) "360.com"
6) "3"
//只列出myzset的元素
127.0.0.1:6379> zrange myzset 0 -1 
1) "baidu.com"
2) "google.com"
3) "360.com"
```

#### 进阶操作

##### 获取集合数据总量

```redis
zcard key
zcount key min max
```

##### 集合交、并集操作

```redis
zinterstore destination numkeys key [key …]
zunionstore destination numkeys key [key …]
```

#### sorted_set类型数据操作的注意事项
score保存的数据存储空间是64位，如果是整数范围是-9007199254740992~9007199254740992
score保存的数据也可以是一个双精度的double值，基于双精度浮点数的特征，可能会丢失精度，使用时候要慎重
sorted_set底层存储还是基于set结构的，因此数据不能重复，如果重复添加相同的数据，score值将被反复覆盖，保留最后一次修改的结果

