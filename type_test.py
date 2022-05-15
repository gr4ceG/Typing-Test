import curses 
from curses import wrapper
import time 
import random

import mysql.connector

def my_input(stdscr, prompt_string): # reads input 
    curses.echo() 
    stdscr.addstr(1, 0, prompt_string)
    stdscr.refresh()
    input = stdscr.getstr(1, len("Please enter your username: "), 20)
    return input

def view_stats(stdscr, name):
    stdscr.clear()

    userstr = 'Hello ' + name + '!'
    stdscr.addstr(0,0, userstr)

    mydb = mysql.connector.connect(
        host="localhost",
        user="testuser",
        password="testpassword"
    )

    mycursor = mydb.cursor()
    mycursor.execute("SELECT * from user_info.users where username = %s", [name])
    myresult = mycursor.fetchall()

    tot_tests = myresult[0][2]
    high_wpm = myresult[0][3]
    tot_wpm = myresult[0][4]

    if tot_tests == 0:
        stdscr.addstr("\nThis is the number of tests you've typed: 0")
        stdscr.addstr("\nThis is your highest Gross WPM: N/A")
        stdscr.addstr("\nThis is your average Gross WPM: N/A")
    else:
        str1 = "This is the number of tests you've typed: " + str(tot_tests)
        stdscr.addstr(1, 0, str1)
        str2 = "This is your highest Gross WPM: " + str(high_wpm)
        stdscr.addstr(2, 0, str2)
        str3 = "This is your average Gross WPM: " + str(round(tot_wpm/tot_tests, 2))
        stdscr.addstr(3, 0, str3)

    mydb.close()

    stdscr.addstr(5, 0, "Press any key to start typing...")
    stdscr.getkey()

def start_screen(stdscr): 
    gameplay = True

    stdscr.clear()

    stdscr.addstr("Welcome to the Speed Typing Test!")
    username = my_input(stdscr, "Please enter your username: ")

    encoding = 'utf-8'
    name = str(username, encoding)

    mydb = mysql.connector.connect(
        host="localhost",
        user="testuser",
        password="testpassword"
    )

    mycursor = mydb.cursor()

    mycursor.execute("SELECT count(*) from user_info.users where username = %s", [username])
    myresult = mycursor.fetchall()

    if myresult[0][0] == 0: # registering new user 

        sql = "INSERT INTO user_info.users (username, password, tot_tests, high_wpm, tot_wpm) VALUES (%s, %s, 0, 0, 0)"
        val = (name, "temp")
        mycursor.execute(sql, val)
        mydb.commit()

    mydb.close()

    userstr = 'Welcome ' + name + '! Press'
    stdscr.addstr(3, 0, userstr)

    stdscr.addstr("\n               h - view your stats")
    stdscr.addstr("\n             esc - exit")
    stdscr.addstr("\n   any other key - begin")

    stdscr.refresh()   
    key = stdscr.getkey()

    if ord(key) == 27:
        gameplay = False
    elif ord(key) == 104:
        gameplay = True
        view_stats(stdscr, name)
    else:
        gameplay = True
    
    return gameplay, name


def display_text(stdscr, target, current, wpm): # overlaying text 
    stdscr.addstr(target)

    combText = "WPM: " + str(wpm)
    stdscr.addstr(1, 0, combText)

    for i, char in enumerate(current): # looping through every single character, displaying character on screen
        correct_char = target[i]
        color = curses.color_pair(2)
        if char != correct_char: 
            color = curses.color_pair(3) # incorrect 
        
        stdscr.addstr(0, i, char, color)

def load_text(): # randomized text
    with open("text.txt", "r") as f:
        lines = f.readlines()
        return random.choice(lines).strip()

def wpm_test(stdscr, wpm): 
    target_text = load_text()
    current_text = [] # list for user's text 
    # wpm=0
    start_time = time.time()
    stdscr.nodelay(True) 

    while True: 
        time_elapsed = time.time() - start_time

        if time_elapsed < 1:
            wpm = int(round(len(current_text) / ((1.0 / 60) * 5)))
        else: 
            wpm = int(round(len(current_text) / ((time_elapsed / 60) * 5)))

        if "".join(current_text) == target_text: 
            break

        stdscr.clear()
        display_text(stdscr, target_text, current_text, wpm)
        stdscr.refresh()

        try: 
            key = stdscr.getkey()
        except: 
            continue

        if ord(key) == 27: # escape key was pressed
            break; 
        
        if key in ("KEY_BACKSPACE", '\b', "\x7f"): # checking for backspaces for all OS
            if len(current_text) > 0: # remove last key inputted 
                current_text.pop()
        elif len(current_text) < len(target_text): 
            current_text.append(key)

    return wpm

def main(stdscr): #standard output screen, terminal

    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)

    gameplay = start_screen(stdscr); 
    wpm = 0

    while gameplay[0]: 
        update_wpm = wpm_test(stdscr, wpm) - 1
        stdscr.addstr(3, 0, "You completed the text! Press any key to continue... ")

        mydb = mysql.connector.connect(
            host="localhost",
            user="testuser",
            password="testpassword"
        )

        mycursor = mydb.cursor()

        name = gameplay[1]
        mycursor.execute("UPDATE user_info.users set tot_tests = tot_tests + 1 where username = %s", [name])
        mydb.commit()

        mycursor.execute("SELECT * from user_info.users where username = %s", [name])
        myresult = mycursor.fetchall()

        prev_wpm = round(myresult[0][3])

        if prev_wpm < update_wpm: # updating highest wpm
            sql = "UPDATE user_info.users set high_wpm = %s where username = %s"
            val = (update_wpm, name)
            mycursor.execute(sql, val)
            mydb.commit()

        # update total_wpm
        sql = "UPDATE user_info.users set tot_wpm = tot_wpm + %s where username = %s"
        val = (update_wpm, name)
        mycursor.execute(sql, val)
        mydb.commit()

        mydb.close()

        stdscr.nodelay(False)
        key = stdscr.getkey()

        if ord(key) == 27: 
            y = list(gameplay)
            y[0] = False
            gameplay = tuple(y)

wrapper(main)
    
