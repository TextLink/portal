import json
import pymysql.cursors

connection = pymysql.connect(host='ec2-18-216-226-115.us-east-2.compute.amazonaws.com',
                             user='root',
                             password='secure12',
                             db='portaldb',
                             port=3306,
                             charset='utf8')

cursor = connection.cursor()


def insert(connective, lang, metadata):
    sql = "INSERT INTO `portal_dimlex` (`connective`, `lang`, `metadata`) " \
          "VALUES (%s, %s, %s)"
    cursor.execute(sql, (connective, lang, metadata))

    # connection is not autocommit by default. So you must commit to save
    # your changes.
    connection.commit()


def read():
    sql = "SELECT `id`, `password` FROM `users` WHERE `email`=%s"
    cursor.execute(sql, ('webmaster@python.org',))
    result = cursor.fetchone()
    print(result)


with open('lico_d.json') as json_data:
    d = json.load(json_data)
    for i in d['entry']:
        if i['word'] != "":
            insert(i['word'], "Italian", json.dumps(i))

connection.close()
