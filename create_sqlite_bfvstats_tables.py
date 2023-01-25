import sqlite3, os

def read_query(filename):
    '''
    Reads in a tab-separated SQL query from a file, and returns it as a string
    SQLite DB Browser generates such files
    '''
    with open(filename, 'r') as f:
        query = f.readlines()
        
    query = '\t'.join(query)
    
    return query

def create_bfvstats(filename, connection, cursor):
    query = read_query(filename)
    cursor.execute(query)
    connection.commit()

def create_log(connection, cursor):
    cursor.execute('CREATE TABLE log(skip int, time datetime);')
    connection.commit()
    

if __name__ == '__main__':
    db_file = 'bfvstats.db'
    query_file = 'create_bfvstats_sqlite.txt'
    # Create file, if needed
    if not db_file in os.listdir():
        with open (db_file, 'w') as f:
            pass
            
        # Add tables to database
        con = sqlite3.connect(db_file)
        cur = con.cursor()
        create_log(con, cur)
        create_bfvstats(query_file, con, cur)
