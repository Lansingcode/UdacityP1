# 优达学城数据分析课程P1项目记录

## 第一步 读入数据
我下载的是上海地区的地图数据，由于地图数据过大，截取部分数据进行分析
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

```python 
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET

import cerberus

import schema

OSM_PATH = "../input_data/sample.osm"

NODES_PATH = "../output_data/nodes.csv"
NODE_TAGS_PATH = "../output_data/nodes_tags.csv"
WAYS_PATH = "../output_data/ways.csv"
WAY_NODES_PATH = "../output_data/ways_nodes.csv"
WAY_TAGS_PATH = "../output_data/ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

# UPDATE THIS VARIABLE
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


def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements

    # YOUR CODE HERE
    if element.tag == 'node':
        node_attribs[NODE_FIELDS[0]] = int(element.attrib[node_attr_fields[0]])    # id：int类型
        node_attribs[NODE_FIELDS[1]] = float(element.attrib[node_attr_fields[1]])  # lat：float类型
        node_attribs[NODE_FIELDS[2]] = float(element.attrib[node_attr_fields[2]])  # lon：float类型
        node_attribs[NODE_FIELDS[3]] = element.attrib[node_attr_fields[3]]         # user：string类型
        node_attribs[NODE_FIELDS[4]] = int(element.attrib[node_attr_fields[4]])    # uid：int类型
        node_attribs[NODE_FIELDS[5]] = element.attrib[node_attr_fields[5]]         # version：string类型
        node_attribs[NODE_FIELDS[6]] = int(element.attrib[node_attr_fields[6]])    # changeset：int类型
        node_attribs[NODE_FIELDS[7]] = element.attrib[node_attr_fields[7]]         # timestamp：string类型
        for tag in element.iter('tag'):
            tmp = {}
            tmp[NODE_TAGS_FIELDS[0]] = int(element.attrib['id'])  # id：int类型
            if LOWER_COLON.match(tag.attrib['k']):
                words = tag.attrib['k'].split(':')
                tmp[NODE_TAGS_FIELDS[1]] = words[-1]
                tmp[NODE_TAGS_FIELDS[3]] = ' '.join(words[:-1])
            elif problem_chars.match(tag.attrib['k']):
                pass
            else:
                tmp[NODE_TAGS_FIELDS[1]] = tag.attrib['k']
                tmp[NODE_TAGS_FIELDS[3]] = default_tag_type

            tmp[NODE_TAGS_FIELDS[2]] = clean_data(tag.attrib['v'], mapping)#清理字段数据
            tags.append(tmp)
        # pprint.pprint({'node': node_attribs, 'node_tags': tags})
        return {'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        way_attribs[WAY_FIELDS[0]] = int(element.attrib[way_attr_fields[0]])  # id：int类型
        way_attribs[WAY_FIELDS[1]] = element.attrib[way_attr_fields[1]]       # user：string类型
        way_attribs[WAY_FIELDS[2]] = int(element.attrib[way_attr_fields[2]])  # uid：int类型
        way_attribs[WAY_FIELDS[3]] = element.attrib[way_attr_fields[3]]       # version：string类型
        way_attribs[WAY_FIELDS[4]] = int(element.attrib[way_attr_fields[4]])  # changeset：int类型
        way_attribs[WAY_FIELDS[5]] = element.attrib[way_attr_fields[5]]       # timestamp：string类型

        node_count = 0
        for node in element.iter('nd'):
            tmp = {}
            tmp[WAY_NODES_FIELDS[0]] = int(element.attrib['id'])
            tmp[WAY_NODES_FIELDS[1]] = int(node.attrib['ref'])
            tmp[WAY_NODES_FIELDS[2]] = node_count
            node_count += 1
            way_nodes.append(tmp)
        for tag in element.iter('tag'):
            tmp = {}
            tmp[WAY_TAGS_FIELDS[0]] = int(element.attrib['id'])
            if LOWER_COLON.match(tag.attrib['k']):
                words = tag.attrib['k'].split(':')
                tmp[WAY_TAGS_FIELDS[1]] = words[-1]
                tmp[WAY_TAGS_FIELDS[3]] = ' '.join(words[:-1])
            else:
                tmp[WAY_TAGS_FIELDS[1]] = tag.attrib['k']
                tmp[WAY_TAGS_FIELDS[3]] = default_tag_type
            tmp[WAY_TAGS_FIELDS[2]] = clean_data(tag.attrib['v'], mapping)#清理字段数据
            tags.append(tmp)
        # pprint.pprint({'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags})
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""

    v = cerberus.Validator(schema)
    if v(element) is not True:
        for i in v.errors.items():
            pprint.pprint(i)
        field, errors = list(v.errors.items())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}".format(field, errors)
        error_string = pprint.pformat(errors)
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, str) else v) for k, v in row.items()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
            codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
            codecs.open(WAYS_PATH, 'w') as ways_file, \
            codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
            codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el)
                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])

if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=False)
```

遇到的问题
1. 没有转换数据类型，但是程序没有检验出来
2. k值分解后取出最后一个数据，前几个单词需要再合并成一个string

## 第三步 导入数据库

问题1： csv文件导入数据库时出现  INSERT failed: datatype mismatch
原因：在进行shape_element时没有转换数据格式，同时validate_element函数没有起作用  
在进行了数据类型转换后，数据插入正常

新建或打开数据库
```sql
sqlite3.exe UdaOpenStreetMap.db
```
建表
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

将csv导入数据库
```sql
.mode csv  //csv模式
.separator ","  //分隔符为‘，’
.import nodes.csv nodes
.import nodes_tags.csv nodes_tags
.import ways.csv ways
.import ways_nodes.csv ways_nodes
.import ways_tags.csv ways_tags
```

数据导入过程中也导入了列名，执行以下语句删除  
```sql
delete from nodes_tags where id='id';
delete from ways_tags where id='id';
delete from wyas_nodes where id='id';
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

有些街道和道路的汉语拼音字段缺失或者错误，已经有程序包可以实现根据汉字直接生成汉语拼音，因此可以用在地图数据的中，根据汉字直接生成汉语拼音，这种方式可以降低错误率同时使数据更加完整。
还有一些汉语名称与汉语拼音混在一起，可以检查字符串是否同时包含汉语与英语进行更正。
