from selenium import webdriver
from os import system
from time import time, strftime, gmtime, sleep
import pyfiglet, os, threading

system("cls")
os.system('title TIKTOD V3')
print(pyfiglet.figlet_format("TIKTOD V3", font="slant"))
print("Author: https://github.com/kangoka\n")
print("1. Auto Views\n2. Auto Hearts\n3. Auto Followers\n")
auto = int(input("Select auto: "))
vidUrl = input("TikTok video URL: ")

start = time()
time_elapsed = strftime('%H:%M:%S', gmtime(time() - start))

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--mute-audio")
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
driver = webdriver.Chrome(r"chromedriver.exe", options=chrome_options)
driver.set_window_size(1024, 650)

Views = 0
Hearts = 0
Followers = 0

def beautify(arg):
    return format(arg, ',d').replace(',', '.')

def title1():
    global Views
    while True:
        time_elapsed = strftime('%H:%M:%S', gmtime(time() - start))
        os.system(f'title TIKTOD V3 ^| Views Sent: {beautify(Views)} ^| Elapsed Time: {time_elapsed}')

def title2():
    global Hearts
    while True:
        time_elapsed = strftime('%H:%M:%S', gmtime(time() - start))
        os.system(f'title TIKTOD V3 ^| Hearts Sent: {beautify(Hearts)} ^| Elapsed Time: {time_elapsed}')

def title3():
    global Followers
    while True:
        time_elapsed = strftime('%H:%M:%S', gmtime(time() - start))
        os.system(f'title TIKTOD V3 ^| Followers Sent: {beautify(Followers)} ^| Elapsed Time: {time_elapsed}')
    

def loop1():
    global Views
    sleep(10)
    try:
        driver.find_element_by_xpath("/html/body/div[4]/div[1]/div[3]/div/div[4]/div/button").click()
    except:
        print("> Solve the captcha!")
        driver.refresh()
        loop1()
    try:
        sleep(2)
        driver.find_element_by_xpath("//*[@id=\"sid4\"]/div/div/div/form/div/input").send_keys(vidUrl)
        sleep(1)
        driver.find_element_by_xpath("//*[@id=\"sid4\"]/div/div/div/form/div/div/button").click()
        sleep(5)
        driver.find_element_by_xpath("//*[@id=\"c2VuZC9mb2xsb3dlcnNfdGlrdG9V\"]/div[1]/div/form/button").click()
        driver.refresh()
        Views += 1000
        sleep(150)
        loop1()
    except:
        print("> An error occured. Now will retry again")
        driver.refresh()
        loop1()

def loop2():
    global Hearts
    sleep(10)
    try:
        driver.find_element_by_xpath("/html/body/div[4]/div[1]/div[3]/div/div[2]/div/button").click()
    except:
        print("> Solve the captcha!")
        driver.refresh()
        loop2()
    try:
        sleep(2)
        driver.find_element_by_xpath('//*[@id="sid2"]/div/div/div/form/div/input').send_keys(vidUrl)
        sleep(1)
        driver.find_element_by_xpath('//*[@id="sid2"]/div/div/div/form/div/div/button').click()
        sleep(5)
        driver.find_element_by_xpath('//*[@id="c2VuZE9nb2xsb3dlcnNfdGlrdG9r"]/div[1]/div/form/button').click()
        sleep(6)
        hearts = driver.find_element_by_xpath('//*[@id="c2VuZE9nb2xsb3dlcnNfdGlrdG9r"]/span').text.split()
        Hearts += int(hearts[0])
        sleep(5)
        driver.refresh()
        sleep(640)
        loop2()
    except:
        print("> An error occured. Now will retry again")
        driver.refresh()
        loop2()

def loop3():
    global Followers
    sleep(10)
    try:
        driver.find_element_by_xpath("/html/body/div[4]/div[1]/div[3]/div/div[1]/div/button").click()
    except:
        print("> Solve the captcha!")
        driver.refresh()
        loop3()
    try:
        sleep(2)
        driver.find_element_by_xpath('//*[@id="sid"]/div/div/div/form/div/input').send_keys(vidUrl)
        sleep(1)
        driver.find_element_by_xpath('//*[@id="sid"]/div/div/div/form/div/div/button').click()
        sleep(5)
        driver.find_element_by_xpath().click('//*[@id="c2VuZF9mb2xsb3dlcnNfdGlrdG9r"]/div[1]/div/form/button')
        sleep(6)
        folls = driver.find_element_by_xpath('//*[@id="c2VuZF9mb2xsb3dlcnNfdGlrdG9r"]/span').text.split()
        Followers += int(folls[0])
        driver.refresh()
        sleep(310)
        loop3()
    except:
        print("> An error occured. Now will retry again")
        driver.refresh()
        loop3()

system("cls")
print(pyfiglet.figlet_format("TIKTOD V3", font="slant"))
print("Author: https://github.com/kangoka\n")
print("Error Log:")

if auto == 1:
    driver.get("https://ketuy.com/")
    a = threading.Thread(target=title1)
    b = threading.Thread(target=loop1)
    a.start()
    b.start()
elif auto == 2:
    driver.get("https://ketuy.com/")
    a = threading.Thread(target=title2)
    b = threading.Thread(target=loop2)
    a.start()
    b.start()
elif auto == 3:
    driver.get("https://ketuy.com/")
    a = threading.Thread(target=title3)
    b = threading.Thread(target=loop3)
    a.start()
    b.start()
else:
    print("Input between 1-3")
