import sqlite3

# Cache for frequently accessed data
cache = {}

class ShortTermMemory:
    def __init__(self):
        self.data = []
        self.time_limit = 60  # seconds

    def add_data(self, data):
        self.data.append(data)
        if len(self.data) > 10:
            self.flush_to_database()

    def flush_to_database(self):
        if self.data:
            with sqlite3.connect('responses.db') as conn:
                c = conn.cursor()
                c.executemany('INSERT INTO short_term_memory (question, response, timestamp) VALUES (?, ?, datetime("now", "localtime"))', self.data)
                conn.commit()
            self.data = []

class LongTermMemory:
    def __init__(self):
        self.data = []

    def add_data(self, data):
        self.data.append(data)
        with sqlite3.connect('responses.db') as conn:
            c = conn.cursor()
            c.execute('INSERT INTO long_term_memory (question, response) VALUES (?, ?)', data)
            conn.commit()

def connect_to_database(db_file):
    conn = sqlite3.connect(db_file)
    return conn

def create_table(conn, table_name):
    c = conn.cursor()
    if table_name == 'responses':
        c.execute('''
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                response TEXT NOT NULL
            )
        ''')
    elif table_name == 'short_term_memory':
        c.execute('''
            CREATE TABLE IF NOT EXISTS short_term_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                response TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
    elif table_name == 'long_term_memory':
        c.execute('''
            CREATE TABLE IF NOT EXISTS long_term_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                response TEXT NOT NULL
            )
        ''')
    conn.commit()

def insert_data_into_table(conn, table_name, data):
    c = conn.cursor()
    if table_name == 'short_term_memory':
        c.execute('INSERT INTO {} (question, response, timestamp) VALUES (?, ?, datetime("now", "localtime"))'.format(table_name), data)
    else:
        c.execute('INSERT INTO {} (question, response) VALUES (?, ?)'.format(table_name), data)
    conn.commit()

def select_data_from_table(conn, table_name, conditions=None):
    c = conn.cursor()
    if conditions:
        c.execute('SELECT * FROM {} WHERE {}'.format(table_name, conditions))
    else:
        c.execute('SELECT * FROM {}'.format(table_name))
    data = c.fetchall()
    return data

def update_data_in_table(conn, table_name, data, conditions=None):
    c = conn.cursor()
    if isinstance(data[0], tuple):
        # Update multiple rows at once
        placeholders = ','.join(['(?, ?)' for _ in range(len(data))])
        if conditions:
            c.execute('UPDATE {} SET response=? WHERE {}'.format(table_name, conditions), data)
        else:
            c.execute('UPDATE {} SET response=?'.format(table_name), data)
        conn.commit()
    else:
        # Update single row
        if conditions:
            c.execute('UPDATE {} SET response=? WHERE {}'.format(table_name, conditions), data)
        else:
            c.execute('UPDATE {} SET response=?'.format(table_name), data)
        conn.commit()
