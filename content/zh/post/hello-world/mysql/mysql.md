+++
title = "MySQL"
date = 2025-03-17T20:06:34+08:00
translationKey = "mysql"
tags = ["数据库", "MySQL"]
categories = ["技术", "后端开发"]

[params]
toc = true
+++

### 参考网站

[自学SQL网(教程 视频 练习全套)](http://xuesql.cn/)

> 学完知识就有题做

__________________

[](https://www.zhihu.com/question/30357711)

[MySQL 教程 | 菜鸟教程](https://www.runoob.com/mysql/mysql-tutorial.html)

[MySQL总结_sq连表-CSDN博客](https://blog.csdn.net/weixin_43896929/article/details/120750965)

[主键 - SQL教程 - 廖雪峰的官方网站](https://liaoxuefeng.com/books/sql/relational/primary-key/index.html)

> 观感最好的教程



## 关系模型

> 引用自 [关系模型 - SQL教程 - 廖雪峰的官方网站](https://liaoxuefeng.com/books/sql/relational/index.html)

### 主键

在关系数据库中，一张表中的每一行数据被称为一条记录。一条记录就是由多个字段组成的。例如，`students`表的两行记录：

| id   | class id | name | gender | score |
| ---- | -------- | ---- | ------ | ----- |
| 1    | 1        | 小明 | M      | 90    |
| 2    | 1        | 小红 | F      | 95    |

对于关系表，有个很重要的约束，就是**任意两条记录不能重复**。不能重复不是指两条记录不完全相同，而是指**能够通过某个字段唯一区分出不同的记录**，这个字段被称为***主键***。

例如，假设我们把`name`字段作为主键，那么通过名字`小明`或`小红`就能唯一确定一条记录。但是，这么设定，就没法存储同名的同学了，因为**插入相同主键的两条记录是不被允许的**。

对主键的要求，最关键的一点是：记录一旦插入到表中，**主键最好不要再修改，因为主键是用来唯一定位记录的**，修改了主键，会造成一系列的影响。

由于主键的作用十分重要，如何选取主键会对业务开发产生重要影响。如果我们以学生的身份证号作为主键，似乎能唯一定位记录。然而，身份证号也是一种业务场景，如果身份证号升位了，或者需要变更，作为主键，不得不修改的时候，就会对业务产生严重影响。

所以，选取主键的一个基本原则是：**不使用任何业务相关的字段作为主键**。

因此，身份证号、手机号、邮箱地址这些看上去可以唯一的字段，均*不可*用作主键。

作为主键最好是完全业务无关的字段，我们一般把这个字段命名为`id`。常见的可作为`id`字段的类型有：

1. 自增整数类型：数据库会在插入数据时自动为每一条记录分配一个自增整数，这样我们就完全不用担心主键重复，也不用自己预先生成主键；
2. 全局唯一GUID类型：也称UUID，使用一种全局唯一的字符串作为主键，类似`8f55d96b-8acc-4636-8cb8-76bf8abc2f57`。GUID算法通过网卡MAC地址、时间戳和随机数保证任意计算机在任意时间生成的字符串都是不同的，大部分编程语言都内置了GUID算法，可以自己预算出主键。

对于大部分应用来说，通常自增类型的主键就能满足需求。我们在`students`表中定义的主键也是`BIGINT NOT NULL AUTO_INCREMENT`类型。

> 如果使用INT自增类型，那么当一张表的记录数超过2147483647（约21亿）时，会达到上限而出错。使用BIGINT自增类型则可以最多约922亿亿条记录。

  

#### 小结

主键是关系表中记录的唯一标识。主键的选取非常重要：主键不要带有业务含义，而应该使用BIGINT自增或者GUID类型。主键也不应该允许`NULL`。

可以使用多个列作为联合主键，但联合主键并不常用。  



### 外键

当我们用主键唯一标识记录时，我们就可以在`students`表中确定任意一个学生的记录：

| id   | name | other columns... |
| ---- | ---- | ---------------- |
| 1    | 小明 | ...              |
| 2    | 小红 | ...              |

我们还可以在`classes`表中确定任意一个班级记录：

| id   | name | other columns... |
| ---- | ---- | ---------------- |
| 1    | 一班 | ...              |
| 2    | 二班 | ...              |

但是我们如何确定`students`表的一条记录，例如，`id=1`的小明，属于哪个班级呢？

由于一个班级可以有多个学生，在关系模型中，这两个表的关系可以称为“一对多”，即一个`classes`的记录可以对应多个`students`表的记录。

为了表达这种一对多的关系，我们需要在`students`表中加入一列`class_id`，让它的值与`classes`表的某条记录相对应：

| id   | class_id | name | other columns... |
| ---- | -------- | ---- | ---------------- |
| 1    | 1        | 小明 | ...              |
| 2    | 1        | 小红 | ...              |
| 5    | 2        | 小白 | ...              |

这样，我们就可以根据`class_id`这个列直接定位出一个`students`表的记录应该对应到`classes`的哪条记录。

- 小明的`class_id`是`1`，因此，对应的`classes`表的记录是`id=1`的一班；
- 小红的`class_id`是`1`，因此，对应的`classes`表的记录是`id=1`的一班；
- 小白的`class_id`是`2`，因此，对应的`classes`表的记录是`id=2`的二班。



在`students`表中，通过`class_id`的字段，**可以把数据与另一张表关联起来**，这种列称为`外键`。

外键并不是通过列名实现的，而是通过定义外键约束实现的：

```mysql
ALTER TABLE students
ADD CONSTRAINT fk_class_id
FOREIGN KEY (class_id)
REFERENCES classes (id);
```

其中，外键约束的名称`fk_class_id`可以任意，`FOREIGN KEY (class_id)`指定了`class_id`作为外键，`REFERENCES classes (id)`指定了这个外键将关联到`classes`表的`id`列（即`classes`表的主键）。

通过定义外键约束，关系数据库可以保证无法插入无效的数据。即如果`classes`表不存在`id=99`的记录，`students`表就无法插入`class_id=99`的记录。

由于外键约束会降低数据库的性能，大部分互联网应用程序为了追求速度，并不设置外键约束，而是仅靠应用程序自身来保证逻辑的正确性。这种情况下，`class_id`仅仅是一个普通的列，只是它起到了外键的作用而已。

要删除一个外键约束，也是通过`ALTER TABLE`实现的：

```mysql
ALTER TABLE students
DROP FOREIGN KEY fk_class_id;
```

注意：删除外键约束并没有删除外键这一列。删除列是通过`DROP COLUMN ...`实现的。



#### 多对多

通过一个表的外键关联到另一个表，我们可以定义出一对多关系。有些时候，还需要定义“多对多”关系。例如，一个老师可以对应多个班级，一个班级也可以对应多个老师，因此，班级表和老师表存在多对多关系。

多对多关系实际上是通过两个一对多关系实现的，即通过一个中间表，关联两个一对多关系，就形成了多对多关系：

`teachers`表：

| id   | name   |
| ---- | ------ |
| 1    | 张老师 |
| 2    | 王老师 |
| 3    | 李老师 |
| 4    | 赵老师 |

`classes`表：

| id   | name |
| ---- | ---- |
| 1    | 一班 |
| 2    | 二班 |

中间表`teacher_class`关联两个一对多关系：

| id   | teacher_id | class_id |
| ---- | ---------- | -------- |
| 1    | 1          | 1        |
| 2    | 1          | 2        |
| 3    | 2          | 1        |
| 4    | 2          | 2        |
| 5    | 3          | 1        |
| 6    | 4          | 2        |

通过中间表`teacher_class`可知`teachers`到`classes`的关系：

- `id=1`的张老师对应`id=1,2`的一班和二班；
- `id=2`的王老师对应`id=1,2`的一班和二班；
- `id=3`的李老师对应`id=1`的一班；
- `id=4`的赵老师对应`id=2`的二班。

同理可知`classes`到`teachers`的关系：

- `id=1`的一班对应`id=1,2,3`的张老师、王老师和李老师；
- `id=2`的二班对应`id=1,2,4`的张老师、王老师和赵老师；

因此，通过中间表，我们就定义了一个“多对多”关系。



#### 一对一

一对一关系是指，一个表的记录对应到另一个表的唯一一个记录。

例如，`students`表的每个学生可以有自己的联系方式，如果把联系方式存入另一个表`contacts`，我们就可以得到一个“一对一”关系：

| id   | student_id | mobile      |
| ---- | ---------- | ----------- |
| 1    | 1          | 135xxxx6300 |
| 2    | 2          | 138xxxx2209 |
| 3    | 5          | 139xxxx8086 |

有细心的童鞋会问，既然是一对一关系，那为啥不给`students`表增加一个`mobile`列，这样就能合二为一了？

如果业务允许，完全可以把两个表合为一个表。但是，有些时候，如果某个学生没有手机号，那么，`contacts`表就不存在对应的记录。实际上，一对一关系准确地说，是`contacts`表一对一对应`students`表。

还有一些应用会把一个大表拆成两个一对一的表，目的是把经常读取和不经常读取的字段分开，以获得更高的性能。例如，把一个大的用户表分拆为用户基本信息表`user_info`和用户详细信息表`user_profiles`，大部分时候，只需要查询`user_info`表，并不需要查询`user_profiles`表，这样就提高了查询速度。



#### 小结

关系数据库通过外键可以实现一对多、多对多和一对一的关系。外键既可以通过数据库来约束，也可以不设置约束，仅依靠应用程序的逻辑来保证。



### 索引

在关系数据库中，如果有上万甚至上亿条记录，在查找记录的时候，想要获得非常快的速度，就需要使用索引。

索引是关系数据库中对某一列或多个列的值进行预排序的数据结构。通过使用索引，可以让数据库系统不必扫描整个表，而是直接定位到符合条件的记录，这样就大大加快了查询速度。

例如，对于`students`表：

| id   | class_id | name | gender | score |
| ---- | -------- | ---- | ------ | ----- |
| 1    | 1        | 小明 | M      | 90    |
| 2    | 1        | 小红 | F      | 95    |
| 3    | 1        | 小军 | M      | 88    |

如果要经常根据`score`列进行查询，就可以对`score`列创建索引：

```sql
ALTER TABLE students
ADD INDEX idx_score (score);
```

使用`ADD INDEX idx_score (score)`就创建了一个名称为`idx_score`，使用列`score`的索引。索引名称是任意的，索引如果有多列，可以在括号里依次写上，例如：

```sql
ALTER TABLE students
ADD INDEX idx_name_score (name, score);
```

索引的效率取决于索引列的值是否散列，即该列的值如果越互不相同，那么索引效率越高。反过来，如果记录的列存在大量相同的值，例如`gender`列，大约一半的记录值是`M`，另一半是`F`，因此，对该列创建索引就没有意义。

可以对一张表创建多个索引。索引的优点是提高了查询效率，缺点是在插入、更新和删除记录时，需要同时修改索引，因此，索引越多，插入、更新和删除记录的速度就越慢。

对于主键，关系数据库会自动对其创建主键索引。使用主键索引的效率是最高的，因为主键会保证绝对唯一。



#### 唯一索引

在设计关系数据表的时候，看上去唯一的列，例如身份证号、邮箱地址等，因为他们具有业务含义，因此不宜作为主键。

但是，这些列根据业务要求，又具有唯一性约束：即不能出现两条记录存储了同一个身份证号。这个时候，就可以给该列添加一个唯一索引。例如，我们假设`students`表的`name`不能重复：

```sql
ALTER TABLE students
ADD UNIQUE INDEX uni_name (name);
```

通过`UNIQUE`关键字我们就添加了一个唯一索引。

也可以只对某一列添加一个唯一约束而不创建唯一索引：

```sql
ALTER TABLE students
ADD CONSTRAINT uni_name UNIQUE (name);
```

这种情况下，`name`列没有索引，但仍然具有唯一性保证。

无论是否创建索引，对于用户和应用程序来说，使用关系数据库不会有任何区别。这里的意思是说，当我们在数据库中查询时，如果有相应的索引可用，数据库系统就会自动使用索引来提高查询效率，如果没有索引，查询也能正常执行，只是速度会变慢。因此，索引可以在使用数据库的过程中逐步优化。



#### 小结

通过对数据库表创建索引，可以提高查询速度；

通过创建唯一索引，可以保证某一列的值具有唯一性；

数据库索引对于用户和应用程序来说都是透明的。



## SELECT 查询

```sql
SELECT column, another_column, …
FROM mytable
WHERE condition
    AND/OR another_condition
    AND/OR …;
    
SELECT * FROM movies 
WHERE year>=2010 AND length_minutes<120;
```

### **筛选数字属性列**

| 关键字 |  | 例 |
| --- | --- | --- |
| =, !=, < <=, >, ≥ |  | col_name != 4 |
| BETWEEN … AND … | 在两个数之间 | col_name BETWEEN 1.5 AND 10.5 |
| NOT BETWEEN … AND … |  | col_name NOT BETWEEN 1 AND 10 |
| IN (…) | 在一个列表 | col_name IN (2, 4, 6) |
| NOT IN (…) |  | col_name NOT IN (1, 3, 5) |

### **筛选字符串属性列**

|  |  |  |
| --- | --- | --- |
| = | 完全等于 |  |
| != or <>  | 不等于 |  |
| LIKE | 没有用通配符等价于 = |  |
| NOT LIKE | 没有用通配符等价于 != |  |
| % | 通配符 | col_name LIKE "%AT%” |
| _(下划线) |  | col_name LIKE "AN_” |

```sql
/*通配符*/
col_name LIKE "%AT%";
/*"AT""AT*...""...*AT""...*AT*..."均满足条件
 "AT"前后可以有任意字符*/
col_name LIKE "AN_";
/*"AND"可以 "AN""ANDD"均不行
 与'%'相似 但只代表一个字符*/
```

### 过滤/排序

```sql
/*用DISTINCT关键字来指定某个或某些属性列唯一返回*/
SELECT DISTINCT column, another_column, …
FROM mytable
WHERE condition(s);
```

```sql
/*让结果按一个或多个属性列做排序*/
SELECT column, another_column, …
FROM mytable
WHERE condition(s)
/* ASC 升序或 DESC 降序*/
ORDER BY column ASC/DESC
/*LIMIT来指定只返回多少行结果 
 用OFFSET来指定从哪一行开始返回*/
LIMIT num_limit OFFSET num_offset;
/*关于OFFSET 若要输出第N行(及之后)
  则OFFSET的参数须为N-1 */
```

#### 例题

![例题1](MySQL/Screenshot_2025-03-11_132438.png)

---



### SELECT复习题

![例题2](MySQL/Screenshot_2025-03-11_134213.png)

---



### **在查询中使用表达式**

实际上AS不仅用在表达式别名上，普通的属性列甚至是表（table）都可以取一个别名，这让SQL更容易理解

```sql
--属性列和表取别名的例子
SELECT column AS better_column_name, …
FROM a_long_widgets_table_name AS mywidgets
INNER JOIN widget_sales
  ON mywidgets.id = widget_sales.widget_id;
```

```sql
--包含表达式的例子
SELECT  particle_speed / 2.0 AS half_particle_speed --对结果做了一个除2
FROM physics_data
WHERE ABS(particle_position) * 10.0 >500
            --（条件要求这个属性绝对值乘以10大于500）;
```

![例题3](MySQL/Screenshot_2025-03-13_164705.png)

---



### **在查询中进行统计**

![样图1](MySQL/v2-89b10c80ff69acdb02494042f55c59d2_1440w.webp)

```sql
SELECT AGG_FUNC(column_or_expression) AS aggregate_description, …
FROM mytable
WHERE constraint_expression;
```

常用统计函数:

| Function | Description |
| --- | --- |
| COUNT(*) COUNT(column) | 计数！COUNT(*) 统计数据行数，COUNT(column) 统计column非NULL的行数 |
| MIN(column) | 找column最小的一行 |
| MAX(column) | 找column最大的一行 |
| AVG(column) | 对column所有行取平均值 |
| SUM(column) | 对column所有行求和 |

---



### 分组统计

`GROUP BY` 数据分组语法可以按某个`col_name`对数据进行分组，如：`GROUP BY Year`指对数据按年份分组， 相同年份的分到一个组里。如果把统计函数和`GROUP BY`结合，那统计结果就是对分组内的数据统计了
`GROUP BY` 分组结果的数据条数，就是分组数量，比如：`GROUP BY Year`，全部数据里有几年，就返回几条数据， 不管是否应用了统计函数

```sql
--用分组的方式统计
SELECT AGG_FUNC(column_or_expression) AS aggregate_description, …
FROM mytable
WHERE constraint_expression
GROUP BY column;
```

![例题4](MySQL/Screenshot_2025-03-13_170736.png)

在 **`GROUP BY`** 分组语法中，我们知道数据库是先对数据做 **`WHERE`** ，然后对结果做分组，如果我们要对分组完的数据再筛选出几条如何办？
一个不常用的语法 **`HAVING`** 语法将用来解决这个问题，他可以对分组之后的数据再做`SELECT`筛选

**`HAVING`** 和 **`WHERE`** 语法一样，只不过作用的结果集不一样. 在我们例子数据表数据量小的情况下可能感觉 **`HAVING`** 没有什么用，但当你的数据量成千上万属性又很多时也许能帮上大忙

---



### JOIN 连接

#### 数据库范式

数据库范式是数据表设计的规范，在范式规范下，数据库里每个表存储的重复数据降到最少(这有助于数据的一致性维护)同时在数据库范式下，表和表之间不再有很强的数据耦合，可以独立的增长(ie. 比如汽车引擎的增长和汽车的增长是完全独立的)  



```sql
SELECT column, another_table_column, …
FROM mytable --主表
INNER JOIN another_table --要连接的表
    ON mytable.id = another_table.id 
    --想象一下刚才讲的主键连接，两个相同的连成1条
WHERE condition(s)
ORDER BY column, … ASC/DESC
LIMIT num_limit OFFSET num_offset;
```

本例中`ON`条件描述的关联关系:

####  **`INNER JOIN`** (内)连接

 先将两个表数据连接到一起，两个表中如果通过ID互相找不到的数据将会舍弃。此时，你可以将连表后的数据看作两个表的合并，SQL中的其他语句会在这个合并基础上 继续执行(想一下和之前的单表操作就一样了)
还有一个理解 **``INNER JOIN``** 的方式，就是把 **`INNER JOIN`** 想成两个集合的交集。

![例题5](C:/Users/Kawauso/Documents/Blogs/source/_posts/MySQL/Screenshot_2025-03-11_142245.png)

####   `OUTER JOIN`外连接

```sql
--用LEFT/RIGHT/FULL JOINs 做多表查询
SELECT column, another_column, …
FROM mytable
INNER/LEFT/RIGHT/FULL JOIN another_table
    ON mytable.id = another_table.matching_id
WHERE condition(s)
ORDER BY column, … ASC/DESC
LIMIT num_limit OFFSET num_offset;
```

在表A 连接 B， **`LEFT JOIN`** 保留A的所有行，不管有没有能匹配上B，反过来 **`RIGHT JOIN`**则保留所有B里的行。最后**`FULL JOIN`** 不管有没有匹配上，同时保留A和B里的所有行

将两个表数据1-1连接，保留A或B的原有行，如果某一行在另一个表不存在，会用 `NULL`来填充结果数据。

![例题6](C:/Users/Kawauso/Documents/Blogs/source/_posts/MySQL/Screenshot_2025-03-11_151348.png)

---



### 查询执行顺序

![样图2](MySQL/v2-d414289449f1dcaaa8c81e13de989b57_1440w.webp)

```sql
--这才是完整的SELECT查询
SELECT DISTINCT column, AGG_FUNC(column_or_expression), …
FROM mytable
    JOIN another_table
      ON mytable.column = another_table.column
    WHERE constraint_expression
    GROUP BY column
    HAVING constraint_expression
    ORDER BY column ASC/DESC
    LIMIT count OFFSET COUNT;
```

#### 1. `FROM` 和 `JOIN`

**`FROM`** 或  **`JOIN`** 会第一个执行，确定一个整体的数据范围. 如果要JOIN不同表，可能会生成一个临时Table来用于 下面的过程。总之第一步可以简单理解为确定一个数据源表（含临时表）

#### **2. `WHERE`**

我们确定了数据来源 **`WHERE`** 语句就将在这个数据源中按要求进行数据筛选，并丢弃不符合要求的数据行，所有的筛选col属性 只能来自 **`FROM`** 圈定的表. `AS`别名还不能在这个阶段使用，因为可能别名是一个还没执行的表达式

#### **3. `GROUP BY`**

如果你用了 **`GROUP BY`** 分组，那 **`GROUP BY`** 将对之前的数据进行分组，统计等，并将是结果集缩小为分组数.这意味着 其他的数据在分组后丢弃.

#### **4. `HAVING`**

如果你用了 **``GROUP BY``** 分组, **`HAVING`** 会在分组完成后对结果集再次筛选。`AS`别名也不能在这个阶段使用.

#### **5. `SELECT`**

确定结果之后， **`SELECT`** 用来对结果col简单筛选或计算，决定输出什么数据.

#### **6. `DISTINCT`**

如果数据行有重复 **`DISTINCT`** 将负责排重.

#### **7. `ORDER BY`**

在结果集确定的情况下， **`ORDER BY`** 对结果做排序。因为 **`SELECT`** 中的表达式已经执行完了。此时可以用`AS`别名.

#### **8. `LIMIT` / `OFFSET`**

最后 **`LIMIT`** 和 **`OFFSET`** 从排序的结果中截取部分数据.

#### **结论**

不是每一个SQL语句都要用到所有的句法，但灵活运用以上的句法组合和深刻理解SQL执行原理将能在SQL层面更好的解决数据问题，而不用把问题 都抛给程序逻辑.

---



## NULL

如果某个字段你没有填写到数据库，很可能就会出现 **`NULL`**  。所有一个常见的方式就是为字段设置 **``默认值``** ,比如 数字的默认值设置为0，字符串设置为  ``""`` 字符串. 但是在一些 **`NULL`** 表示它本来含义的场景，需要注意是否设置默认值还是保持 **`NULL`** 。 (比如, 当你计算一些行的平均值的时候，如果是0会参与计算导致平均值差错，是  **`NULL`** 则不会参与计算).

还有一些情况很难避免 **``NULL``** 的出现, 比如之前说的 outer-joining 多表连接，A和B有数据差异时，必须用 **``NULL``** 来填充。这种情况，可以用 **`IS NULL`** 和 **``IS NOT NULL``** 来选在某个字段是否等于 **``NULL``**.

```sql
SELECT column, another_column, …
FROM mytable
WHERE column IS/IS NOT NULL
AND/OR another_condition
AND/OR …;
```

![例题7](MySQL/Screenshot_2025-03-11_203039.png)

---



## 修改数据

> 部分引用自 [修改数据 - SQL教程 - 廖雪峰的官方网站](https://liaoxuefeng.com/books/sql/manipulation/index.html)

关系数据库的基本操作就是增删改查，即CRUD：Create、Retrieve、Update、Delete。其中，对于查询，我们已经详细讲述了`SELECT`语句的详细用法。

而对于增、删、改，对应的SQL语句分别是：

- INSERT：插入新记录；
- UPDATE：更新已有记录；
- DELETE：删除已有记录。

我们将分别讨论这三种修改数据的语句的使用方法。

#### INSERT 插入

引用于 [MySQL 插入数据 | 菜鸟教程](https://www.runoob.com/mysql/mysql-insert-query.html)

例如，我们向`user`表插入一条新记录，先列举出需要插入的字段名称，然后在`VALUES`子句中依次写出对应字段的值：

```sql
INSERT INTO table_name (column1, column2, column3, ...)
VALUES (value1, value2, value3, ...);
--
INSERT INTO users (username, email, birthdate, is_active)
VALUES ('test', 'test@runoob.com', '1990-01-01', true);
```

如果要插入所有列(即插入行)的数据，可以省略列名：

```sql
INSERT INTO users
VALUES (NULL,'test', 'test@runoob.com', '1990-01-01', true);
```

还可以一次性添加多条记录，只需要在`VALUES`子句中指定多个记录值，每个记录是由`(...)`包含的一组值，每组值用逗号`,`分隔：

```sql
INSERT INTO users (username, email, birthdate, is_active)
VALUES
    ('test1', 'test1@runoob.com', '1985-07-10', true),
    ('test2', 'test2@runoob.com', '1988-11-25', false),
    ('test3', 'test3@runoob.com', '1993-05-03', true);
```

---

### UPDATE 更新

[MySQL UPDATE 更新 | 菜鸟教程](https://www.runoob.com/mysql/mysql-update-query.html)

```sql
UPDATE table_name
SET column1 = value1, column2 = value2, ...
WHERE condition;
```

**参数说明：**

- `table_name` 是你要更新数据的表的名称。
- `column1`, `column2`, ... 是你要更新的列的名称。
- `value1`, `value2`, ... 是新的值，用于替换旧的值。
- `WHERE condition` 是一个可选的子句，用于指定更新的行。如果省略 `WHERE` 子句，将更新表中的所有行。

**更多说明：**

- 你可以同时更新一个或多个字段。
- 你可以在 `WHERE` 子句中指定任何条件。
- 你可以在一个单独表中同时更新数据。

当你需要更新数据表中指定行的数据时 `WHERE` 子句是非常有用的。

```sql
--更新单个列的值
UPDATE employees
SET salary = 60000
WHERE employee_id = 101;
```

```sql
--更新多个列的值
UPDATE orders
SET status = 'Shipped', ship_date = '2023-03-01'
WHERE order_id = 1001;
```

```sql
--使用表达式更新值
UPDATE products
SET price = price * 1.1
WHERE category = 'Electronics';
```

```sql
--更新使用子查询的值
UPDATE customers
SET total_purchases = (
    SELECT SUM(amount)
    FROM orders
    WHERE orders.customer_id = customers.customer_id
)
WHERE customer_type = 'Premium';
```



在使用MySQL这类真正的关系数据库时，`UPDATE`语句会返回更新的行数以及`WHERE`条件匹配的行数。

例如，更新`id=1`的记录时：

```plain
mysql> UPDATE students SET name='大宝' WHERE id=1;
Query OK, 1 row affected (0.00 sec)
Rows matched: 1  Changed: 1  Warnings: 0
```

MySQL会返回`1`，可以从打印的结果`Rows matched: 1 Changed: 1`看到。

当更新`id=999`的记录时：

```plain
mysql> UPDATE students SET name='大宝' WHERE id=999;
Query OK, 0 rows affected (0.00 sec)
Rows matched: 0  Changed: 0  Warnings: 0
```

MySQL会返回`0`，可以从打印的结果`Rows matched: 0 Changed: 0`看到。

---



### DELETE 删除

`DELETE`语句的基本语法是：

```sql
DELETE FROM <表名> WHERE ...;
```

例如，我们想删除`students`表中`id=1`的记录，就需要这么写：

```mysql
-- 删除id=1的记录:
DELETE FROM students WHERE id=1;
-- 查询并观察结果:
SELECT * FROM students;
```

注意到`DELETE`语句的`WHERE`条件也是用来筛选需要删除的行，因此和`UPDATE`类似，`DELETE`语句也可以一次删除多条记录：

```mysql
-- 删除id=5,6,7的记录:
DELETE FROM students WHERE id>=5 AND id<=7;
-- 查询并观察结果:
SELECT * FROM students;
```

如果`WHERE`条件没有匹配到任何记录，`DELETE`语句不会报错，也不会有任何记录被删除。例如：

```mysql
-- 删除id=999的记录:
DELETE FROM students WHERE id=999;
-- 查询并观察结果:
SELECT * FROM students;
```

最后，要特别小心的是，和`UPDATE`类似，不带`WHERE`条件的`DELETE`语句会删除整个表的数据：

```sql
DELETE FROM students;
```

这时，整个表的所有记录都会被删除。所以，在执行`DELETE`语句时也要非常小心，最好先用`SELECT`语句来测试`WHERE`条件是否筛选出了期望的记录集，然后再用`DELETE`删除。 



在使用MySQL这类真正的关系数据库时，`DELETE`语句也会返回删除的行数以及`WHERE`条件匹配的行数。

例如，分别执行删除`id=1`和`id=999`的记录：

```plain
mysql> DELETE FROM students WHERE id=1;
Query OK, 1 row affected (0.01 sec)

mysql> DELETE FROM students WHERE id=999;
Query OK, 0 rows affected (0.01 sec)
```

---



## CREATE 创建

[MySQL 创建数据表 | 菜鸟教程](https://www.runoob.com/mysql/mysql-create-tables.html)

```sql
--用户表实例
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    birthdate DATE,
    is_active BOOLEAN DEFAULT TRUE
);
```

实例解析：

- `id`: 用户 id，整数类型，自增长，作为主键。
- `username`: 用户名，变长字符串，不允许为空。
- `email`: 用户邮箱，变长字符串，不允许为空。
- `birthdate`: 用户的生日，日期类型。
- `is_active`: 用户是否已经激活，布尔类型，默认值为 true。

以上只是一个简单的实例，用到了一些常见的数据类型包括`INT`, `VARCHAR`, `DATE`, `BOOLEAN`，可以根据实际需要选择不同的数据类型。

`AUTO_INCREMENT` 关键字用于创建一个自增长的列，`PRIMARY KEY` 用于定义主键。

如果希望在创建表时指定数据引擎，字符集和排序规则等，可以使用 **`CHARACTER SET`** 和 **`COLLATE`** 子句：

```sql
CREATE TABLE mytable (
    id INT PRIMARY KEY,
    name VARCHAR(50)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```
