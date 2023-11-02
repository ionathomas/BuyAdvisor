import pymysql

global db


def openDbConnection(dbConnection):
    global db
    db = dbConnection


def queryDB(query):
    global db
    with db.cursor() as cursor:
        try:
            sql_exec = cursor.execute(query)
            if sql_exec:
                return sql_exec, cursor
            else:
                return 0, 0
        except (pymysql.Error, pymysql.Warning) as e:
            print(f'error! {e}')
            return 0, 0


def addRecord(query):
    sql_exec, cursor = queryDB(query)
    if sql_exec:
        print(sql_exec)
        print("Record Added")
        return True
    else:
        print(sql_exec)
        print("Not Added")
        return False


def getRecords(query):
    sql_exec, cursor = queryDB(query)
    if sql_exec:
        print(sql_exec)
        result = cursor.fetchall()
        print("Record(s) Found")
        return list(result)
    else:
        print(sql_exec)
        print("No Record")
        return []


def editRecord(query):
    sql_exec, cursor = queryDB(query)
    if sql_exec:
        print(sql_exec)
        print("Record Updated")
        return True
    else:
        print(sql_exec)
        print("Not Updated")
        return False


def deleteRecord(query):
    sql_exec, cursor = queryDB(query)
    if sql_exec:
        print(sql_exec)
        print("Record Deleted")
        return True
    else:
        print(sql_exec)
        print("Not Deleted")
        return False


def closeDbConnection():
    global db
    db.close()
