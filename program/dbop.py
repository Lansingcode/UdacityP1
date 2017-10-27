# -*- coding:utf-8 -*-

import sqlite3
query='select * from nodes_tags limit 10;'

conn=sqlite3.connect('UdaOpenStreetMap.db')
c=conn.cursor()
c.execute(query)
data=c.fetchall()
for i in data:
    print i
