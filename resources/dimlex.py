import json
import pymysql.cursors

connection = pymysql.connect(host='localhost',
                             user='root',
                             password='keaton',
                             db='portal',
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


with open('dimlex_eng.json') as json_data:
    d = json.load(json_data)
    for i in d['entry']:
        if i['word'] != "":
            insert(i['word'], "English", json.dumps(i))

connection.close()
