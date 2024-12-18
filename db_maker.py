import sqlite3

db = sqlite3.connect("new_db.db")

c = db.cursor()

c.execute('''
    CREATE TABLE [user_info] (
        [user_id] INTEGER PRIMARY KEY,
        [user_chat_state] TEXT
        );
          ''')

c.execute('''
    CREATE TABLE [channels] (
        [channel_id] INTEGER PRIMARY KEY,
        [user_id] INTEGER,
        [user_channel] TEXT);
          ''')  

c.execute('''
    CREATE TABLE [lots] (
        [lot_id] INTEGER PRIMARY KEY,
        [user_id] INTEGER,
        [text] TEXT,
        [file] INTEGER,
        [participation] TEXT,
        [winners_count] INTEGER,
        [channel_id] INTEGER,
        [date] TEXT,
        [end_count] INTEGER
        [end_date] TEXT,
        [players] TEXT
          );
          ''') 



# c.execute('''
# CREATE TABLE [formula_text] (
#     [fot_id] INTEGER PRIMARY KEY,
#     [fot_lang] TEXT,
#     [fot_code] TEXT,
#     [fot_content] TEXT,
#     [fot_date] TEXT,
#     [fot_time] TEXT,
#     [user_id] INTEGER)
# ''')

# c.execute('''
#     create TABLE [sentences] (
#   [id] INTEGER PRIMARY KEY,
#   [_text] TEXT,
#   [user] TEXT,
#   [_type] INTEGER,
#   [lang] TEXT,
#   [_version] INTEGER)
# ''')

# c.execute('''
#     create TABLE [relation_skepsi] (
#       [fos_id] INTEGER PRIMARY KEY,
#       [fos_id_a] INTEGER,
#       [fos_id_b] INTEGER,
#       [res_type] INTEGER,
#       [res_author] INTEGER,
#       [res_date] TEXT,
#       [res_time] TEXT)
# ''')

db.close()
