+++
title = "Redis"
date = 2025-03-18T15:41:00+08:00
translationKey = "redis"
tags = ["Cache", "Persistence", "Database"]
categories = ["Tech", "Backend Development"]

[params]
toc = true
+++

Redis (Remote Dictionary Server) is a high-performance, open-source, in-memory data structure store, used as a database, cache, and message broker.

### References  

[知乎 超强、超详细Redis入门教程](https://zhuanlan.zhihu.com/p/411888708)  

[CSDN【Redis二三事】一套超详细的Redis学习教程（步骤图片+实操）---第一集](https://blog.csdn.net/wenwenaier/article/details/121878831)

> Detailed, with real business scenario examples.

## Data Structures  

Redis includes five major data types: string (`string`), list (`list`), hash (`hash`), set (`set`), and sorted set (`zset`).  

### string  

The most basic data type in Redis. Each key corresponds to a value, which can be text, numbers, or binary data, with a maximum storage of 512MB. It supports operations like string concatenation, substring, increment, and decrement, and is suitable for scenarios such as caching data, counters (e.g., page view statistics), and distributed locks.  

#### Basic Operations  

```redis
set key value
get key
del key 
```

##### Add/Modify Multiple Data  

```redis
mset key1 value1 key2 value2...
```

##### Get Multiple Data  

```redis
mget key1 key2...
```

##### Get Character Count of Data  

```redis
strlen key
// For example
set name1 nosql
strlen name1
// Output: 5
```

##### Append Information  

```redis
append key value
// For example
append name1 name
get name1
/* Output: nosqlname*/
```

##### Multi-data vs Single-data Operations  

- Executing $n$ commands individually requires 1 send + 1 process + 1 return $n$ times
- Executing $n$ commands via a multi-data command requires 1 send + $n$ processes + 1 return
- When the data volume is large, the time consumed by multi-data commands is much less than individual commands
  
#### Advanced Operations  

##### Increment/Decrement Numeric Data by a Specified Range

```redis
incrby key increment
decrby key increment
```

##### Numeric Operations on String Types  

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

When encountering numeric operations, Redis will automatically convert the string type into a number.  

#### Considerations for String Type Numeric Operations  

- Differences between execution status feedback and normal data manipulation feedback
  - Indicates whether the operation results were successful
    - (integer) 0 -> false Failed
    - (integer) 1 -> true Succeeded
  - Indicates the resulting value
    - (integer) 3 -> 3      3 items
    - (integer) 1 -> 1      1 item
- Data not found
  - (`nil`) is equivalent to `null`
- Maximum data storage capacity
  - 512MB
- Maximum range for numeric calculations (maximum value of `long` in `java`)
  - 9223372036854775807
  
---

### hash

Similar to a small key-value store, suitable for storing structured data such as user information (ID, name, email, etc.). Compared to the `String` type, it saves more memory because multiple fields share the same key. You can operate on fields individually to avoid reading and modifying the entire object, making it suitable for storing objects, session information, etc.  

#### Basic Operations  

```redis
hset key field value // Add/Modify data
hget key field // Get data
hgetall key
hdel key field1 [field2]
```

##### Add/Modify Multiple Data  

```redis
hmset key field1 value1 field2 value2
```

##### Get Multiple Data  

```redis
hmget key field1 field2...
```

##### Get the Number of Fields in a Hash Table

```redis
hlen key
```

##### Check if a Specified Field Exists in a Hash Table

```redis
hexists key field
```



#### Advanced Operations  

##### Get All Field Names or Field Values in a Hash Table  

```redis
hkeys key
hvals key
```

##### Increment the Numeric Value of a Specified Field by a Certain Range

```redis
hincrby key field increment
```

##### Comprehensive Example

```redis
// Create hash and assign values
127.0.0.1:6379> HMSET user:001 username antirez password P1pp0 age 34 
OK
// List the contents of the hash
127.0.0.1:6379> HGETALL user:001 
1) "username"
2) "antirez"
3) "password"
4) "P1pp0"
5) "age"
6) "34"
// Change a specific value in the hash
127.0.0.1:6379> HSET user:001 password 12345 
(integer) 0
// List the contents of the hash again
127.0.0.1:6379> HGETALL user:001 
1) "username"
2) "antirez"
3) "password"
4) "12345"
5) "age"
6) "34"
```

#### Considerations for Hash Type Data Operations

- 1. The `value` under the `hash` type **can only store strings**, and no other data types are allowed, so there is no nesting. If no data is found, the corresponding value is (`nil`).
- 2. Each `hash` can store 2^23-1 key-value pairs.
- 3. The `hash` type is very close to the data storage format of objects, and object properties can be flexibly added. However, its initial design was not meant for storing large numbers of objects. Remember not to abuse it, and **never use a hash as an object list**.
- 4. The `hgetall` operation can retrieve all properties. If there are too many `field`s inside, traversing the whole data will be very inefficient and may become a bottleneck for data access.

---

### list

Based on a doubly linked list, it allows fast insertion and deletion of elements from the head (left) or tail (right), and supports reading elements by specifying an index range. It is suitable for implementing message queues, timelines (such as Weibo feeds), task scheduling, and other applications, especially for scenarios that require processing data according to insertion order.

#### Basic Operations  

##### Add/Modify Data

```redis
lpush key value1 [value2]... // Push from the left
rpush key value1 [value2]... /* Push from the right */
```

##### Get Data

About `lrange`:  

- `lrange` is used to get elements within a specified range  
- -1 represents the last element  
- List element indexing starts from position 0  

```redis
lrange key start stop
lindex key index
lien key
```

##### Get and Remove Data

```redis
lpop key
rpop key
```

##### Remove Specified Data

About `lrem`:  

- Parameter `count`
  - `count > 0` -> Remove `count` matching `value`s starting from the head (left)
  - `count < 0` -> Remove `count` matching `value`s starting from the tail (right)
  - `count = 0` -> Remove **all matching `value`s** (equivalent to removing all elements with this value from the list)
- If `key` does not exist
  - Returns 0
- Commonly used to **remove duplicate elements from a list or clean up data**

```redis
lrem key count value
```



#### Advanced Operations  

##### Get and Remove Data Within a Specified Time  

About `blpop`:  

- Parameter `key1 [key2...]`
  - Multiple list keys can be provided, and `Redis` will check these lists in order sequentially
- Parameter `timeout`
  - timeout > 0 -> If the list is empty, wait up to `timeout` seconds
  - timeout < 0 -> Block **indefinitely** until data is available
- Applicable to scenarios like **task queues, producer-consumer models**, etc.

```redis
blpop key1 [key2] timeout
brpop key1 [key2] timeout
```

Example  

```redis
RPUSH list1 "a" "b" "c"    // List content: ["a", "b", "c"]
BLPOP list1 10             // Pop "a", returns ["list1", "a"]
BLPOP list1 10             // Pop "b", returns ["list1", "b"]
BLPOP list1 10             // Pop "c", returns ["list1", "c"]
BLPOP list1 10             /* List is empty, blocks for up to 10 seconds; if no new elements, returns nil */
```

##### Comprehensive Example

```redis
// Create a new list called mylist and insert element "1" at the head
127.0.0.1:6379> lpush mylist "1" 
// Returns the current number of elements in mylist
(integer) 1 
// Insert element "2" on the right side of mylist
127.0.0.1:6379> rpush mylist "2" 
(integer) 2
// Insert element "0" on the left side of mylist
127.0.0.1:6379> lpush mylist "0" 
(integer) 3
// List elements in mylist from index 0 to 1
127.0.0.1:6379> lrange mylist 0 1 
1) "0"
2) "1"
// List elements in mylist from index 0 to the last element
127.0.0.1:6379> lrange mylist 0 -1 
1) "0"
2) "1"
3) "2"
```

#### Considerations for List Type Data Operations  

- 1. The data stored in a `list` is of the `string` type, and the total data capacity is limited to a maximum of 2^32-1 elements.  
- 2. A `list` has the concept of "indexes," but manipulating data is usually done in the form of a "queue" (enqueue/dequeue) or a "stack" (push/pop).  
- 3. When retrieving all data, the end index is set to -1.  
- 4. A `list` allows `pagination` of data; typically, page 1 information comes from the `list`, while page 2 and more are loaded in a "database" fashion.  

---

### set

It consists of unique, unordered elements, supporting addition, deletion, and search operations with O(1) time complexity, and provides set operations like intersection, union, and difference. Suitable for applications like deduplication, mutual follows in recommendation systems, and tag management. Because duplicate elements are not allowed, it efficiently stores collections of distinct data.

#### Basic Operations

##### Add Data

```redis
sadd key member1 [member2]
```

##### Get All Data

```redis
smembers key
```

##### Delete Data

```redis
srem key member1 [member2]
```

##### Get Total Amount of Set Data

```redis
scard key
```

##### Check if Specified Data is in the Set

```redis
sismember key member
```

#### Advanced Operations

##### Randomly Get a Specified Number of Elements from the Set

```redis
srandmember key [count]
```

##### Randomly Get an Element from the Set and Remove It

```redis
spop key
```

##### Calculate the Intersection, Union, and Difference of Two Sets

```redis
sinter key1 [key2]
sunion key1 [key2]
sdiff key1 [key2]
```

##### Calculate the Intersection, Union, and Difference of Two Sets and Store in a Specified Set

```redis
sinterstore destination key1 [key2]
sunionstore destination key1 [key2]
sdiffstore destination key1 [key2]
```

##### Move Specified Data from the Source Set to the Destination Set

```redis
smove source destination member
```



##### Comprehensive Example

```redis
// Add a new element "one" to the set myset
127.0.0.1:6379> sadd myset "one" 
(integer) 1
127.0.0.1:6379> sadd myset "two"
(integer) 1
// List all elements in the set myset
127.0.0.1:6379> smembers myset 
1) "one"
2) "two"
// Check if element "one" is in the set myset, returning 1 indicates existence
127.0.0.1:6379> sismember myset "one" 
(integer) 1
// Check if element "three" is in the set myset, returning 0 indicates non-existence
127.0.0.1:6379> sismember myset "three" 
(integer) 0
// Create a new set yourset
127.0.0.1:6379> sadd yourset "1" 
(integer) 1
127.0.0.1:6379> sadd yourset "2"
(integer) 1
127.0.0.1:6379> smembers yourset
1) "1"
2) "2"
// Take the union of the two sets
127.0.0.1:6379> sunion myset yourset 
1) "1"
2) "one"
3) "2"
4) "two"
```

#### Considerations for Set Type Data Operations

- The set type `does not allow duplicate data`. If the added data already exists in the set, only `one copy will be kept`.
- Although set has the `same storage structure` as hash, it `cannot utilize the space for storing values` in the hash.



### zset

Builds upon Set by adding a score to each element and ordering them by this score, supporting ranged queries, score-based ranking, and other operations. Suitable for leaderboards (like game scores), priority queues (like scheduled tasks), and time-sorted data storage (like article reading rankings), where sorting by weight is needed.

#### Basic Operations

##### Add Data

```redis
zadd key score1 member1 [score2 member2]
```

##### Get All Data

```redis
zrange key start stop [WITHSCORES]     // Display in ascending order
zrevrange key start stop [WITHSCORES]  // Display in descending order
```

##### Delete Data

```redis
zrem key member [member...]
```

##### Get Data by Condition

```redis
zrangebyscore key min max [Withscores][limit]
zrevrangebyscore key max min [withscores]
```

##### Delete Data by Condition

```redis
zremrangebyrank key start stop  // Delete by index
zremrangebyscore key min max 	// Delete by range
```

##### Comprehensive Example

```redis
// Add a new sorted set myzset, insert the element baidu.com, and assign it score 1:
127.0.0.1:6379> zadd myzset 1 baidu.com 
(integer) 1
// Add the element 360.com to myzset, assigning it score 3
127.0.0.1:6379> zadd myzset 3 360.com 
(integer) 1
// Add the element google.com to myzset, assigning it score 2
127.0.0.1:6379> zadd myzset 2 google.com 
(integer) 1
// List all elements of myzset along with their scores, showing that myzset is already ordered.
127.0.0.1:6379> zrange myzset 0 -1 with scores 
1) "baidu.com"
2) "1"
3) "google.com"
4) "2"
5) "360.com"
6) "3"
// List only the elements of myzset
127.0.0.1:6379> zrange myzset 0 -1 
1) "baidu.com"
2) "google.com"
3) "360.com"
```

#### Advanced Operations

##### Get Total Amount of Set Data

```redis
zcard key
zcount key min max
```

##### Set Intersection and Union Operations

```redis
zinterstore destination numkeys key [key …]
zunionstore destination numkeys key [key …]
```

#### Considerations for sorted_set Type Data Operations
The data storage space for the score is 64-bit; for an integer, the range is -9007199254740992 to 9007199254740992.
The data saved in the score can also be a double-precision floating-point number. Based on the characteristics of double-precision floating-point numbers, precision might be lost, so it should be used with caution.
The underlying storage of sorted_set is still based on the set structure. Therefore, data cannot be duplicated. If identical data is added repeatedly, the score value will simply be overwritten repeatedly, keeping the result of the last modification.
