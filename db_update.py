import sqlite3
con = sqlite3.connect('bfvstats.db')
cur = con.cursor()

last_run = cur.execute(
    'SELECT skip FROM log ORDER BY skip DESC LIMIT 1;').fetchall()
total = cur.execute('SELECT COUNT(*) FROM log;').fetchall()
samples = cur.execute('SELECT COUNT(*) FROM bfvstats').fetchone()

# con.commit()
con.close()
print(last_run, total, samples)
