import pymysql

global db


# Function to open connection to DB
def openDbConnection(dbConnection):
    global db
    db = dbConnection


# Function to query the DB
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


# Insert Query Function
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


# Reading from the Table Function
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


# Update Query Function
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


# Delete Query Funtion
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


# Close the DB table connection
def closeDbConnection():
    global db
    db.close()
