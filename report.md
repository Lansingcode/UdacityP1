# 优达学城数据分析课程P1项目记录

## 第一步 读入数据
数据取自[OpenStreetMap](https://www.openstreetmap.org)，下载上海地区地图数据，由于地图数据过大，截取部分数据进行分析，截取后未压缩的OSM数据大小为79M  

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET  # Use cElementTree or lxml if too slow

# OSM_FILE = "some_osm.osm"  # Replace this with your osm file
OSM_FILE='shanghai_china.osm'
SAMPLE_FILE = "../input_data/sample.osm"

k = 10 # Parameter: take every k-th top level element

def get_element(osm_file, tags=('node', 'way', 'relation')):
    # 生成器，每次调用，返回osm文件中的一个节点
    """Yield element if it is the right type of tag
    Reference:
    http://stackoverflow.com/questions/3095434/inserting-newlines-in-xml-file-generated-via-xml-etree-elementtree-in-python
    """
    context = iter(ET.iterparse(osm_file, events=('start', 'end')))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()

with open(SAMPLE_FILE, 'wb') as output:
    output.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
    output.write(b'<osm>\n  ')

    # Write every kth top level element
    for i, element in enumerate(get_element(OSM_FILE)):
        if i % k == 0:
            output.write(ET.tostring(element, encoding='utf-8'))

    output.write(b'</osm>')
```

## 第二步 清洗数据

代码说明
- osm文件放在input_data文件夹中，输出的csv文件放在output_data文件夹中，代码放在program文件夹中，三个文件夹在同一目录下

源数据中的问题
1. 道路和街道的英文名标注不统一，比如有的街道为st，有的为St.，有的道路标注为Rd
经过数据清理后，街道英文名统一为Street，道路统一为Road，Ave统一为Avenue，核心代码如下，详细代码见`program/schema_data.py`

```python 

mapping = {"St": "Street",
           "St.": "Street",
           'Str': 'Street',
           'Ave': 'Avenue',
           'Ave.': 'Avenue',
           'Rd.': 'Road',
           'Rd': 'Road',
           'rd': 'Road',
           'Lu': 'Road'
           }


def clean_data(name, mapping):
    """清洗数据函数"""
    words = name.split()
    if words[-1] in mapping:
        words[-1] = mapping[words[-1]]
        name = ' '.join(words)
    return name
```

遇到的问题
1. 没有转换数据类型，但是程序没有检验出来
2. k值分解后取出最后一个数据，前几个单词需要再合并成一个string

## 第三步 导入数据库

问题1： csv文件导入数据库时出现  INSERT failed: datatype mismatch
原因：在进行shape_element时没有转换数据格式，同时validate_element函数没有起作用  
在进行了数据类型转换后，数据插入正常

1. 新建或打开数据库
```sql
sqlite3.exe UdaOpenStreetMap.db
```
2. 建表
```sql
CREATE TABLE nodes (
    id INTEGER PRIMARY KEY NOT NULL,
    lat REAL,
    lon REAL,
    user TEXT,
    uid INTEGER,
    version INTEGER,
    changeset INTEGER,
    timestamp TEXT
);

CREATE TABLE nodes_tags (
    id INTEGER,
    key TEXT,
    value TEXT,
    type TEXT,
    FOREIGN KEY (id) REFERENCES nodes(id)
);

CREATE TABLE ways (
    id INTEGER PRIMARY KEY NOT NULL,
    user TEXT,
    uid INTEGER,
    version TEXT,
    changeset INTEGER,
    timestamp TEXT
);

CREATE TABLE ways_tags (
    id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    type TEXT,
    FOREIGN KEY (id) REFERENCES ways(id)
);

CREATE TABLE ways_nodes (
    id INTEGER NOT NULL,
    node_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    FOREIGN KEY (id) REFERENCES ways(id),
    FOREIGN KEY (node_id) REFERENCES nodes(id)
);
```

3. 将csv导入数据库
```sql
.mode csv  //csv模式
.separator ","  //分隔符为‘，’
.import nodes.csv nodes
.import nodes_tags.csv nodes_tags
.import ways.csv ways
.import ways_nodes.csv ways_nodes
.import ways_tags.csv ways_tags
```

4. 数据导入过程中也导入了列名，执行以下语句删除  
```sql
delete from nodes_tags where id='id';
delete from ways_tags where id='id';
delete from wyas_nodes where id='id';
```

5. 插入数据后查看数据库表
```sql
sqlite> select count(*) from nodes;
387694
sqlite> select count(*) from nodes_tags;
28544
sqlite> select count(*) from ways;
47292
sqlite> select count(*) from ways_tags;
98376
sqlite> select count(*) from ways_nodes;
460424
```
6. 唯一用户数量
```sql
sqlite> select count(distinct(t.uid)) from (select n.user,n.uid from nodes as n
union select w.user,w.uid from ways as w) as t;
1545
```
7. node数量
```sql
sqlite> select count(distinct(id)) from nodes;
387694
```
8. way数量
```sql
sqlite> select count(distinct(id)) from ways;
47292
```
9. 商店节点数量
```sql
sqlite> select count(distinct(id)) from nodes_tags where key='shop';
244
```
# 第四步 在数据库中探索数据

1. 找出对地图贡献最多的前十名用户  

```sql
sqlite> select user,uid,count(*) as num from nodes group by uid order by num desc limit 10;
user,uid,num
"Chen Jia",288524,61589
"Austin Zhu",4816761,21613
aighes,110639,17320
xiaotu,2215592,14797
katpatuka,17497,13532
iberutan,5888135,11404
XBear,42537,11346
yangfl,304705,10009
Peng-Chung,3182193,9785
Holywindon,1436097,9585
```

2. 在nodes表中对选择结果对lat降序排序时发现，这个地区所有的用户大部分都是同一个人，有可能是该用户属于某个专门负责更新地图的组织并负责该地区的数据更新  

```sql
sqlite> select lat,user from nodes order by lat desc limit 10;
lat,user
32.4719975,"Chen Jia"
32.471995,dmgroom_ct
32.471993,"Chen Jia"
32.4719929,"Chen Jia"
32.4719828,"Chen Jia"
32.4719815,"Chen Jia"
32.4719786,"Chen Jia"
32.4719664,"Chen Jia"
32.471954,"Chen Jia"
32.4719442,"Chen Jia"
```

## 第五步 数据处理的问题和发现的一些错误

1. 在我的工程中只更改了字符串中最后一个单词，字符串中间的单词错误并没有更改，例如
```html
<tag k="name:en" v="Guilin Rd  Shanghai Railstation (S)" />
```
2. 有些地点中文标注正确但是英文标注不正确，例如
```html
<tag k="name" v="宜兴市 (Taixing)" />
```

## 第六步 改进意见

有些街道和道路的汉语拼音字段缺失或者错误，已经有程序包可以实现根据汉字直接生成汉语拼音，因此可以用在地图数据的中，根据汉字直接生成汉语拼音，这种方式可以降低错误率同时使数据更加完整，但是对一些多音字或者特殊读音的汉字还是会标注错误。还有一些汉语名称与汉语拼音混在一起，可以检查字符串是否同时包含汉语与英语进行更正。
