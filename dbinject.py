import sqlite3

DB_PATH = "data/economy.db"

def give_balls(user_id: int, bonus_balls: int):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT balance FROM economy WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if row:
            new_balance = row[0] + bonus_balls
            cur.execute("UPDATE economy SET balance = ? WHERE user_id = ?", (new_balance, user_id))
            print(f"Gave {bonus_balls} balls to {user_id}. New balance: {new_balance}")
        else:
            cur.execute("INSERT INTO economy (user_id, balance, last_daily) VALUES (?, ?, NULL)", (user_id, bonus_balls))
            print(f"User {user_id} didn't exist. Created and gave {bonus_balls} balls.")

#give_balls(1313117547486515273, 500)

give_balls(1186872689038729237, 1000)