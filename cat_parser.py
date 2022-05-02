# categories parser from Polyakov website

from selenium import webdriver
from selenium import common
from selenium.webdriver.common.by import By
from time import sleep
import json

LINK = "https://kpolyakov.spb.ru/school/ege/generate.htm"

categories = dict()


def add_cat(ege_id, data):
    # add category to cats.json
    try:
        with open("cats.json", "r", encoding="utf-8") as j:
            all_cats = json.loads(j.read())
    except FileNotFoundError:
        with open("cats.json", "w", encoding="utf-8") as j:
            j.write("{}")
            all_cats = dict()

    ege_id = (ege_id.split()[-1])
    all_cats[ege_id] = dict()
    for line in data.split('\n'):
        cat_id, cat_name = line.split(":", 1)
        cat_id = cat_id.split()[-1]
        cat_name = cat_name[1:]
        all_cats[ege_id][cat_id] = cat_name

    with open("cats.json", "w", encoding="utf-8") as j:
        j.write(json.dumps(all_cats))


with webdriver.Firefox(executable_path="./geckodriver") as dr:
    # parser
    dr.get(LINK)
    select = dr.find_element(By.ID, "egeId")
    options = select.find_elements(By.TAG_NAME, "option")
    button = dr.find_element(By.XPATH, "//input[@value='Найти все задачи']")
    for i in range(len(options)):
        # parse all tasks
        opt = options[i]
        opt.click()  # select option
        sleep(0.1)
        button.click()  # go to page
        sleep(0.25)
        # page
        ege_id_tag = dr.find_element(By.CLASS_NAME, "title").text
        print(ege_id_tag)
        try:
            cats = dr.find_element(By.XPATH, "//p[contains(text(), 'Раздел')]")  # find cats
            add_cat(ege_id_tag.replace('–', '-'), cats.text)  # fix wrong "-" and add category to file
        except common.exceptions.NoSuchElementException:
            print("Тут нету разделов...")
            pass

        dr.back()

        # reload page
        select = dr.find_element(By.ID, "egeId")
        options = select.find_elements(By.TAG_NAME, "option")
        button = dr.find_element(By.XPATH, "//input[@value='Найти все задачи']")

dr.close()
