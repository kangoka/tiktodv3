from selenium import webdriver
from selenium.webdriver.support.ui import Select
from colorama import init
from colorama import Fore, Back, Style
import pyfiglet
from os import system
import time

chrome_options = webdriver.ChromeOptions()
#chrome_options.add_argument("--headless")
chrome_options.add_argument("--log-level=3")
driver = webdriver.Chrome(r"chromedriver.exe", options=chrome_options)
driver.set_window_size(1024, 650)

i = 0
a = 0
x = 0

def loop1():
    global i
    time.sleep(10)
    try:
        driver.find_element_by_xpath("/html/body/div[3]/div[1]/div[3]/div/div[4]/div/button").click()
    except:
        print("You didn't solve the captcha yet. Need to refresh to avoid endless loop.")
        driver.refresh()
        loop1()
    try:
        time.sleep(2)
        driver.find_element_by_xpath("/html/body/div[3]/div[4]/div/div/div/form/div/input").send_keys(vidUrl)
        time.sleep(1)
        driver.find_element_by_xpath("/html/body/div[3]/div[4]/div/div/div/form/div/div/button").click()
        time.sleep(2)
        driver.find_element_by_xpath("/html/body/div[3]/div[4]/div/div/div/div/div/div[1]/div/form/button").click()
        driver.refresh()
        i += 1
        total = i * 1000
        print("Views success delivered! Total", total,"views")
        time.sleep(20)
        loop1()
    except:
        print("An error occured. Now will retry again")
        driver.refresh()
        loop1()

def loop2():
    global i
    time.sleep(10)
    try:
        driver.find_element_by_xpath("/html/body/div[3]/div[1]/div[3]/div/div[2]/div/button").click()
    except:
        print("You didn't solve the captcha yet. Need to refresh to avoid endless loop.")
        driver.refresh()
        loop2()
    try:
        time.sleep(2)
        driver.find_element_by_xpath("/html/body/div[3]/div[3]/div/div/div/form/div/input").send_keys(vidUrl)
        time.sleep(1)
        driver.find_element_by_xpath("/html/body/div[3]/div[3]/div/div/div/form/div/div/button").click()
        time.sleep(2)
        driver.find_element_by_xpath("/html/body/div[3]/div[3]/div/div/div/div/div[1]/div/form/button").click()
        driver.refresh()
        i += 1
        total = i * 25
        print("Hearts success delivered! Total estimated", total,"hearts")
        time.sleep(110)
        loop2()
    except:
        print("An error occured. Now will retry again")
        driver.refresh()
        loop2()

def loop3():
    def hearts():
        global i, x, a
        x = 0
        time.sleep(10)
        try:
            driver.find_element_by_xpath("/html/body/div[3]/div[1]/div[3]/div/div[2]/div/button").click()
        except:
            print("You didn't solve the captcha yet. Need to refresh to avoid endless loop.")
            driver.refresh()
            hearts()
        try:
            time.sleep(2)
            driver.find_element_by_xpath("/html/body/div[3]/div[3]/div/div/div/form/div/input").send_keys(vidUrl)
            time.sleep(1)
            driver.find_element_by_xpath("/html/body/div[3]/div[3]/div/div/div/form/div/div/button").click()
            time.sleep(2)
            driver.find_element_by_xpath("/html/body/div[3]/div[3]/div/div/div/div/div[1]/div/form/button").click()
            driver.refresh()
            a += 1
            total = a * 25
            print("Hearts success delivered! Total estimated", total,"hearts")
            views()
        except:
            print("An error occured. Now will retry again")
            driver.refresh()
            hearts()

    def views():
        global i, x
        time.sleep(10)
        try:
            driver.find_element_by_xpath("/html/body/div[3]/div[1]/div[3]/div/div[4]/div/button").click()
        except:
            print("You didn't solve the captcha yet. Need to refresh to avoid endless loop.")
            driver.refresh()
            views()
        try:
            time.sleep(2)
            driver.find_element_by_xpath("/html/body/div[3]/div[4]/div/div/div/form/div/input").send_keys(vidUrl)
            time.sleep(1)
            driver.find_element_by_xpath("/html/body/div[3]/div[4]/div/div/div/form/div/div/button").click()
            time.sleep(2)
            driver.find_element_by_xpath("/html/body/div[3]/div[4]/div/div/div/div/div/div[1]/div/form/button").click()
            driver.refresh()
            x += 1
            i += 1
            total = i * 1000
            print("Views success delivered! Total", total,"views")
            if x < 9:
                time.sleep(20)
                views()
            else:
                hearts()
        except:
            print("An error occured. Now will retry again")
            driver.refresh()
            views()

    hearts()

vidUrl = "YOUR_URL" #Change YOUR_URL to your Tik Tok video URL. This URL used to get views or hearts or both

system("cls")
tiktod = pyfiglet.figlet_format("TIKTOD V3", font="slant")
print(tiktod)
print("Author: https://github.com/kangoka")
print("")

"""
You can change auto value below
auto = 1 for auto views
auto = 2 for auto hearts
auto = 3 for auto views + hearts
"""
auto = 1

if auto == 1:
    driver.get("https://vipto.de/")
    loop1()
elif auto == 2:
    driver.get("https://vipto.de/")
    loop2()
else:
    driver.get("https://vipto.de/")
    loop3()
