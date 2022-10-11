import sqlite3

con = sqlite3.connect('bfvstats.db')
cur = con.cursor()

last_run = cur.execute(
    'SELECT skip FROM log ORDER BY skip DESC LIMIT 1').fetchone()[0]

print(f'Began last run by skipping {last_run} profiles')

db_size = cur.execute('SELECT COUNT(*) FROM bfvstats').fetchone()[0]

print(f'There are currently {db_size} records in the db')
con.close()
