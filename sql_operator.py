import sqlite3
import random


class MyTask:
    """
    Task object containing all basic data.
    """
    def __init__(self, pid, ege_id, cat_id, text, file_url='', image_url='', code='', ans=None, solved_res=None):
        # for simplification
        self.id = pid
        self.ege_id = ege_id
        self.cat_id = cat_id
        self.text = text
        self.image_url = image_url
        self.file_url = file_url
        self.code = code
        self.answer = ans
        self.solved = solved_res

    def __repr__(self):
        return f"<Task №{self.id} ({self.ege_id}-{self.cat_id})>"

    def __eq__(self, other):
        return self.id == other.id


class MyUser:
    def __init__(self, user_id, chat_id, task=-1, ege_id=-1, cat_id=-1):
        """
        -1 means that no action is awaited from user.
        Task != -1 means that user if solving some task now, and we should wait for answer.
        """
        self.user_id = user_id
        self.chat_id = chat_id
        self.task = task
        self.ege_id = str(ege_id)
        self.cat_id = str(cat_id)

    def __repr__(self):
        return f"<User{self.user_id} ege_id={self.ege_id} cat={self.cat_id}"


class TasksDB:
    def __init__(self, filename):
        self.con = sqlite3.connect(filename)
        self.cur = self.con.cursor()

    def clean(self):
        """
        Cleans all tasks.
        """
        self.cur.execute("DELETE FROM tasks")

    def add_task(self, pid, ege_id, cat_id, text, image_url, file_url, code, ans):
        """
        Add a task.
        """
        req = f"""INSERT INTO tasks VALUES({pid}, "{ege_id}", {cat_id}, '{text.replace("'", " ")}', "{image_url}", "{file_url}", '{code}', '{ans}')"""
        # print(req)
        try:
            self.cur.execute(req)
            self.con.commit()
        except sqlite3.IntegrityError:
            # already exists
            print("exists")

    def update_user(self, user: MyUser):
        """
        Update user in the db.
        """
        self.cur.execute(f"INSERT INTO users VALUES('{user.user_id}', '{user.chat_id}', '{user.task}', '{user.ege_id}',"
                         f"'{user.cat_id}')")
        self.con.commit()
        return 1

    def get_user(self, user_id):
        """
        Get user by ID.
        """
        user = self.cur.execute(f"SELECT * FROM users WHERE user_id='{user_id}'").fetchone()
        if user:
            return MyUser(user[0], user[1], user[2], user[3], user[4])
        return

    def get_task(self, task_id):
        """
        Get a raw task object.
        """
        task = self.cur.execute(f"SELECT * FROM tasks WHERE id='{task_id}'").fetchone()
        if task:
            return MyTask(task_id, task[1], task[2], task[3], task[4], task[5], task[6], task[7])
        return

    def get_tasks(self, ege_id, cat_id=-1):
        """
        Get all tasks with specific ege_id or category id.
        """
        req = f"SELECT * FROM tasks WHERE ege_id = '{ege_id}'"
        if str(cat_id) != '-1':
            req += f" AND cat='{cat_id}'"
        return list([MyTask(t[0], t[1], t[2], t[3], t[4], t[5], t[6], t[7]) for t in self.cur.execute(req)])

    def get_all_solved(self, user_id, ege_id=-1, cat_id=-1, solved=None):
        """
        Get all solved tasks by a user. A ege_id or cat_id can be specified.
        Solved stands for correctness. None=ant, True=solved right, False=solved wrong.
        """
        req = f"SELECT * from tasks INNER JOIN solved ON user = '{user_id}' AND task == id"
        if str(ege_id) != '-1':
            req += f" AND ege_id = '{ege_id}'"
        if str(cat_id) != '-1':
            req += f" AND cat = '{cat_id}'"
        if solved is not None:
            req += f" AND correct = {int(solved)}"

        res = self.cur.execute(req).fetchall()
        if res:
            return list([MyTask(t[0], t[1], t[2], t[3], t[4], t[5], t[6], t[7], t[8]) for t in res])
        return

    def select_unsolved(self, user_id, ege_id, cat_id=-1):
        """
        Select random unsolved task.
        """
        all_tasks = self.get_tasks(ege_id, cat_id)
        solved_tasks = self.get_all_solved(user_id, ege_id, cat_id)
        if solved_tasks:
            for solved_task in solved_tasks:
                try:
                    all_tasks.remove(solved_task)
                except ValueError:
                    pass
        if all_tasks:
            return random.choice(all_tasks)
        else:
            return None

    def is_solved(self, user_id, task_id):
        """
        Check if task was solved by a user. Returns True/False if was solved, otherwise returns None.
        """
        req = f"SELECT correct FROM solved WHERE user='{user_id}' AND task='{task_id}'"
        res = self.cur.execute(req).fetchone()
        if res is None:
            return None
        else:
            return bool(res[0])

    def solve(self, user_id, task_id, is_right):
        """
        Mark task as solved by user.
        """
        self.cur.execute(f"INSERT INTO solved VALUES ('{user_id}', '{task_id}', '{is_right}')")
        self.con.commit()

    def close(self):
        self.cur.close()
        self.con.close()
