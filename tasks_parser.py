# very bad tasks parser: works avoiding js scripts
# run this very careful, it's desirable to create a backup database

import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from sql_operator import TasksDB
import json
import time


def get_link(task, cat):
    return f"https://kpolyakov.spb.ru/school/ege/gen.php?action=viewAllEgeNo&egeId={task}&cat{cat}=on"


def remove_empty_lines(s):
    out = []
    for line in s.split('\n'):
        if line:
            out.append(line)
    return "\n".join(out)


def load_cats():
    # load task categories from file
    with open("cats.json", 'r') as j:
        return json.loads(j.read())


with webdriver.Firefox(executable_path="./geckodriver") as dr:
    tasks_ids = load_cats()
    db = TasksDB("db.sqlite3")
    # db.clean()

    for task_id in list(tasks_ids.keys()):
        # for each task
        for cat in tasks_ids[task_id]:
            # for each task category
            print(get_link(task_id, cat))
            dr.get(get_link(task_id, cat))

            # execute special script to convert subs and sups to unicode symbols
            with open("replace_pows.js") as script:
                dr.execute_script(script.read())

            tasks = dr.find_elements(By.CLASS_NAME, "topicview")  # find task
            answers = dr.find_elements(By.CLASS_NAME, "answer")  # find answer
            for i, task in enumerate(tasks):
                # for each task
                task_pid = task.text.split(')')[0][3:]  # polyakov ID

                print(task_pid, task_id, cat)
                img_src = ""
                href = ""
                code = ""
                text = task.text

                # check images
                try:
                    img_src = task.find_element(By.TAG_NAME, "img").get_attribute("src")
                except selenium.common.exceptions.NoSuchElementException:
                    pass  # no image

                # check links
                try:
                    hrefs = (task.find_elements(By.TAG_NAME, "a"))
                    href = ' '.join([t.get_attribute("href") for t in hrefs])
                except selenium.common.exceptions.NoSuchElementException:
                    pass  # no links

                # check code
                try:
                    code = task.find_element(By.CLASS_NAME, "code").find_elements(By.CLASS_NAME, "pre")[1].text

                    # replace actual \n with a fix to avoid errors
                    code = code.replace(r"\n", r"|n")

                    # replace line breaks with "-" (eg task #240)
                    if '\\\n' in code:
                        for ln in range(32, 0, -1):
                            code = code.replace('\\\n' + ' ' * ln, '')

                    # after parsing code, remove it from main text
                    text = text.replace(task.find_element(By.CLASS_NAME, "code").text, "")

                except selenium.common.exceptions.NoSuchElementException:
                    pass  # no code

                ans = answers[i]
                # open and read answer
                ans.find_element(By.TAG_NAME, "a").click()
                answer = ans.text.replace("Спрятать ответ\n", "")

                if "undefined" in text:
                    # this may happen if some unknown symbols in sups or subs are detected and cannot be replaced
                    # check replace_pows.js
                    print("WARNING")
                    time.sleep(5)

                # add task to db
                db.add_task(int(task_pid), task_id.replace('–', '-'), cat, remove_empty_lines(text), href, img_src,
                            code, answer)
        break

db.close()
dr.close()
