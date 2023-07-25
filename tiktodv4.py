from selenium import webdriver
from os import system, name

from time import time, strftime, gmtime, sleep
import pyfiglet, os, threading
import chromedriver_autoinstaller
from selenium.webdriver.support.ui import WebDriverWait
from time import sleep
from selenium_stealth import stealth
import undetected_chromedriver as uc


# Check if the current version of chromedriver exists
# and if it doesn't exist, download it automatically,
# then add chromedriver to path

def clear():
    if name == 'nt':
        _ = system('cls')
    else:
        _ = system('clear')

clear()
system('title TIKTOD V3')

print(pyfiglet.figlet_format("TIKTOD V3", font="slant"))
print("Make sure to check Zefoy.com beforehand to see if the option you want to select is available!!!\n")
print("1. Viewbot.\n2. Heartbot.\n3. Followerbot.\n4. Sharebot.\n5. Favorites.\n6. Credits")

auto = int(input("Mode: "))
if auto >= 1 and auto <= 5:
    vidUrl = input("TikTok video URL: ")
    input("Do you want to run in Stealth Mode? Y/N: ")
    if input == "Y" or "y":
        options = uc.ChromeOptions()
        driver = uc.Chrome(use_subprocess=True, options=options) 
        stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        )
        
    else:
        chromedriver_autoinstaller.install()
        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)
        driver = webdriver.Chrome()
    start = time()
    time_elapsed = strftime('%H:%M:%S', gmtime(time() - start))
    options.add_argument("--mute-audio")

    
    


    
    driver.set_window_size(1024, 650)

    Runs = 0
    Hearts = 0
    Followers = 0
    Shares = 0
    Favorites = 0




def beautify(arg):
    return format(arg, ',d').replace(',', '.')

def title1(): # Update the title IF option 1 was picked.
    global Runs
    
    while True:
        time_elapsed = strftime('%H:%M:%S', gmtime(time() - start))
        system(f'title TIKTOD V4 ^| Runs Sent: {beautify(Runs)} ^| Elapsed Time: {time_elapsed}')

def title2(): # Update the title IF option 2 was picked.
    global Hearts

    while True:
        time_elapsed = strftime('%H:%M:%S', gmtime(time() - start))
        system(f'title TIKTOD V3 ^| Hearts Sent: {beautify(Hearts)} ^| Elapsed Time: {time_elapsed}')

def title3(): # Update the title IF option 3 was picked.
    global Followers
    
    while True:
        time_elapsed = strftime('%H:%M:%S', gmtime(time() - start))
        system(f'title TIKTOD V4 ^| Followers Sent: {beautify(Followers)} ^| Elapsed Time: {time_elapsed}')
        
def title4(): # Update the title IF option 4 was picked.
    global Shares
    
    while True:
        time_elapsed = strftime('%H:%M:%S', gmtime(time() - start))
        system(f'title TIKTOD V4 ^| Shares Sent: {beautify(Shares)} ^| Elapsed Time: {time_elapsed}')

def title5(): # Update the title IF option 1 was picked.
    global Favorites
    
    while True:
        time_elapsed = strftime('%H:%M:%S', gmtime(time() - start))
        system(f'title TIKTOD V4 ^| Favorites Sent: {beautify(Favorites)} ^| Elapsed Time: {time_elapsed}')

    
def loop1():
    global Runs

    
    poll_rate = 1
    while True:
        try:
            print("Waiting for cloud flare to be completed")
            driver.find_element("xpath", "/html/body/div[5]/div[2]/form/div/div/div/div/button")
            print("passed!")
            break
        except:
            sleep(1)
    while True:
        try:
            driver.find_element("xpath", "/html/body/div[5]/div[2]/form/div/div/div/div/button")
            sleep(poll_rate)
            
        except:
            print("Captcha successfully complete")
            break
    try:
        sleep(2)
        driver.find_element("xpath", "/html/body/div[6]/div/div[2]/div/div/div[5]/div/button").click()
        
        sleep(1)
        driver.find_element("xpath", "(//INPUT[@type='search'])[4]").send_keys(vidUrl)
        
        sleep(2)
        driver.find_element("xpath", "/html/body/div[10]/div/form/div/div/button").click()

        sleep(2)
        driver.find_element("xpath", "/html/body/div[10]/div/div/div[1]/div/form/button").click()
        
        driver.refresh()
        Runs += 1
        print("[+] Views sended!")
        
        for x in range(300):
            sleep(1)
            print("waiting for reset in", 300-x, end = "\r")

        loop1()
        
    except:
        print("[-] An error occured. Retrying..") 
        driver.refresh()
        loop1()

def loop2():
    global Hearts

    
    poll_rate = 1
    while True:
        try:
            print("Waiting for cloud flare to be completed")
            driver.find_element("xpath", "/html/body/div[5]/div[2]/form/div/div/div/div/button")
            print("passed!")
            break
        except:
            sleep(1)
    while True:
        try:
            driver.find_element("xpath", "/html/body/div[5]/div[2]/form/div/div/div/div/button")
            sleep(poll_rate)
        except:
            print("Captcha successfully complete")
            break
    try:
        sleep(2)
        driver.find_element("xpath", "/html/body/div[6]/div/div[2]/div/div/div[3]/div/button").click()
    except:
        print("Option is Unavailable") 
        print("Please Exit this program and try again Later")
    try:
        sleep(1)
        driver.find_element("xpath", "(//INPUT[@type='search'])[2]").send_keys(vidUrl)
        
        sleep(2)
        driver.find_element("xpath", "(//BUTTON[@type='submit'])[2]").click()
        sleep(2)
        try:
            driver.find_element("xpath", "(//BUTTON[@type='submit'])[3]").click()
        except:
            print("waiting for reset")
            driver.refresh()
            loop2()

        driver.refresh()
        Hearts += 1
        print("[+] Hearts sent!")
            
        for x in range(300):
            sleep(1)
            print("waiting for reset in", 300-x, end = "\r")
        loop2()
        
    except:
        print("[-] An error occured. Retrying..") 
        driver.refresh()
        loop2()

def loop3():
    poll_rate = 1
    while True:
        try:
            print("Waiting for cloud flare to be completed")
            driver.find_element("xpath", "/html/body/div[5]/div[2]/form/div/div/div/div/button")
            print("passed!")
            break
        except:
            sleep(1)
    while True:
        try:
            driver.find_element("xpath", "/html/body/div[5]/div[2]/form/div/div/div/div/button")
            sleep(poll_rate)
        except:
            print("Captcha successfully complete")
            break
    try:
        sleep(2)
        driver.find_element("xpath", "/html/body/div[6]/div/div[2]/div/div/div[2]/div/button").click()
    except:
        print("Option is Unavailable") 
        print("Please Exit this program and try again Later")
    try:
        sleep(1)
        driver.find_element("xpath", "(//INPUT[@type='search'])[1]").send_keys(vidUrl)
        
        sleep(2)
        driver.find_element("xpath", "(//BUTTON[@type='submit'])[1]").click()
        sleep(2)
        try:
            driver.find_element("xpath", "(//BUTTON[@type='submit'])[2]").click()
        except:
            print("waiting for reset")
            driver.refresh()
            loop3()

        driver.refresh()
        Hearts += 1
        print("[+] Followers sent!")
            
        for x in range(300):
            sleep(1)
            print("waiting for reset in", 300-x, end = "\r")
        loop3()
        
    except:
        print("[-] An error occured. Retrying..") 
        driver.refresh()
        loop3()

def loop4():
    global Shares
    poll_rate = 1
    while True:
        try:
            print("Waiting for cloud flare to be completed")
            driver.find_element("xpath", "/html/body/div[5]/div[2]/form/div/div/div/div/button")
            print("passed!")
            break
        except:
            sleep(1)
    while True:
        try:
            driver.find_element("xpath", "/html/body/div[5]/div[2]/form/div/div/div/div/button")
            sleep(poll_rate)
            
        except:
            print("Captcha successfully complete")
            break
        
    try:
        sleep(2)
        driver.find_element("xpath", "/html/body/div[6]/div/div[2]/div/div/div[6]/div/button").click()
        
        sleep(1)
        driver.find_element("xpath", "(//INPUT[@type='search'])[5]").send_keys(vidUrl)
        
        sleep(2)
        driver.find_element("xpath", "/html/body/div[11]/div/form/div/div/button").click()

        sleep(2)
        driver.find_element("xpath", "/html/body/div[11]/div/div/div[1]/div/form/button").click()
        
        driver.refresh()
        Shares += 100
        print("[+] Shares sent!")
        for x in range(300):
            sleep(1)
            print("waiting for reset in", 300-x, end = "\r")
        loop4()
        
    except:
        print("[-] An error occured. Retrying..")
        driver.refresh()
        loop4()
def loop5():
    global Favorites
    poll_rate = 1
    while True:
        try:
            print("Waiting for cloud flare to be completed")
            driver.find_element("xpath", "/html/body/div[5]/div[2]/form/div/div/div/div/button")
            print("passed!")
            break
        except:
            sleep(1)
    while True:
        try:
            driver.find_element("xpath", "/html/body/div[5]/div[2]/form/div/div/div/div/button")
            sleep(poll_rate)
        except:
            print("Captcha successfully complete")
            break
        
    try:
        sleep(2)
        driver.find_element("xpath", "/html/body/div[6]/div/div[2]/div/div/div[7]/div/button").click()
        
        sleep(1)
        driver.find_element("xpath", "(//INPUT[@type='search'])[6]").send_keys(vidUrl)
        
        sleep(2)
        driver.find_element("xpath", "/html/body/div[12]/div/form/div/div/button").click()

        sleep(2)
        driver.find_element("xpath", "/html/body/div[12]/div/div/div[1]/div/form/button").click()
        
        driver.refresh()
        Favorites += 100
        print("[+] Favorites sent!")
        for x in range(300):
            sleep(1)
            print("waiting for reset in", 300-x, end = "\r")
        loop5()
        
    except:
        print("[-] An error occured. Retrying..")
        driver.refresh()
        loop5()



clear()

print(pyfiglet.figlet_format("TIKTOD V3", font="slant"))
print("Log:")

if auto == 1:
    driver.get("https://zefoy.com/")
    
    a = threading.Thread(target=title1)
    b = threading.Thread(target=loop1)
    
    a.start()
    b.start()
    
elif auto == 2:
    # once hearts is fixed
    # driver.get("https://zefoy.com/")
    
    a = threading.Thread(target=title2)
    b = threading.Thread(target=loop2)
    
    a.start()
    b.start()
    
elif auto == 3:
    # driver.get("https://zefoy.com/")
    # once followers is fixed
    a = threading.Thread(target=title3)
    b = threading.Thread(target=loop3)
    
    a.start()
    b.start()
    
elif auto == 4:
    driver.get("https://zefoy.com/")
    
    a = threading.Thread(target=title4)
    b = threading.Thread(target=loop4)
    
    a.start()
    b.start()
elif auto == 5:
    driver.get("https://zefoy.com/")
    
    a = threading.Thread(target=title5)
    b = threading.Thread(target=loop5)
    
    a.start()
    b.start() 

elif auto == 6:
    print("[+] This program was created by @kangoka. [github.com/kangoka]")
    print("[+] This program was origionally uploaded to github.com/kangoka/tiktodv3.")
    print("[+] This program was majorly improved by @XxBi1a. [github.com/XxB1a]")
    print("[+] This program was improved by @Ashwin-Iyer1. [github.com/Ashwin-Iyer1]")
    input('Press ENTER to exit')

    
else:
    print(f"{auto} is not a valid option. Please pick 1, 2, 3, 4, 5, or 6")
