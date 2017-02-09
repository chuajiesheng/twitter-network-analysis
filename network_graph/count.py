from py2neo import Graph
g = Graph(password='!abcd1234')

# Calculate level

init_str = 'MATCH (t:Tweet) WHERE NOT (t)<-[:OF|:REPLY_TO]-(:Tweet) SET t.level = 0 RETURN COUNT(t)'
o = g.run(init_str).data()
print('Level', 0, ':', o[0]['COUNT(t)'])

update_str = 'MATCH (p)<-[:OF|:REPLY_TO]-(c:Tweet) WHERE c.level = {} SET p.level = {} RETURN COUNT(p)'
max_level = 0
for i in range(0, 50):
    s = update_str.format(i, i+1)
    print(s)
    o = g.run(s).data()
    print('Level', i, ':', o[0]['COUNT(p)'])
    if o[0]['COUNT(p)'] <= 0:
        max_level = i
        break

# Calculate aggregate child nodes

init_str = 'MATCH (t:Tweet) WHERE NOT (t)<-[:OF|:REPLY_TO]-(:Tweet) SET t.child_nodes = 0 RETURN COUNT(t)'
o = g.run(init_str).data()
print(0, 'child nodes', ':', o[0]['COUNT(t)'])

update_str = 'MATCH (t2:Tweet)-[r:OF|:REPLY_TO]->(t1:Tweet) ' \
             'WHERE t1.level = {} ' \
             'WITH t1, SUM(t2.child_nodes) AS s, COUNT(t2) as c ' \
             'SET t1.child_nodes = c + s ' \
             'RETURN COUNT(t1)'
for i in range(1, max_level + 1):
    s = update_str.format(i)
    print(s)
    o = g.run(s).data()
    print('Level', i, ':', o[0]['COUNT(t1)'])


