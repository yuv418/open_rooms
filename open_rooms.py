#!/usr/bin/python3

import requests
import json
import pickle

from flask import Flask, render_template, request, flash, session, redirect, url_for
import copy

app = Flask(__name__)
app.config["SECRET_KEY"] = "test"

use_lut = {
        "M": [set()] * 2400,
        "T": [set()] * 2400,
        "W": [set()] * 2400,
        "H": [set()] * 2400,
        "F": [set()] * 2400,
        "S": [set()] * 2400, # S is saturday. Why are there saturday classes????
        "U": [set()] * 2400, # U is sunday???. Why are there sunday classes????
        }
universe = set()

DL_JSON = False

def build_use_lut():
    if DL_JSON:
        sched = requests.get("https://sis.rutgers.edu/soc/api/courses.json?year=2023&term=9&campus=NB")
        sched = sched.json()
        # with open('courses.json', 'w') as c_j:
            # json.dump(sched, c_j)
    else:
        with open('courses.json') as c_j:
            sched = json.load(c_j)

    global universe
    # Go through schedule and build the 
    for item in sched:
        for section in item['sections']:
            for mtg_time in section['meetingTimes']:
                try:
                    start = int(mtg_time['startTimeMilitary'])
                    end = int(mtg_time['endTimeMilitary'])

                    cursor = start
                    while cursor != end:
                        cursor += 1 
                        if cursor % 100 == 60:
                            cursor += 40
                        classroom_name = mtg_time['buildingCode'] + '-' + mtg_time['roomNumber']
                        use_lut[mtg_time['meetingDay']][cursor] = use_lut[mtg_time['meetingDay']][cursor].union({classroom_name})
                        universe = universe.union({classroom_name})
                        # print(cursor)
                except ValueError:
                    # For online classes
                    # print("Skipping online/async class")
                    pass
                except KeyError:
                    print(item)
                    exit()
    # print(use_lut)
    with open("lut.pkl", 'wb') as lut_f: 
        print(universe)
        pickle.dump((use_lut, universe), lut_f)

def load_use_lut():
    global use_lut, universe
    with open('lut.pkl', 'rb') as lut_f:
        use_lut, universe = pickle.load(lut_f)
        # print(universe)

def find_open_rooms(day, start_military_time, end_military_time):
    print(end_military_time, start_military_time)
    if end_military_time <= start_military_time:
        return set() 
    # TODO make an iterator
    
    use_rooms = set()
    cursor = start_military_time 
    while cursor != end_military_time:
        cursor += 1
        if cursor % 100 == 60:
            cursor += 40
        use_rooms = use_rooms.union(use_lut[day][cursor])
         
    # print(universe == use_rooms)
    # print(universe.difference(use_rooms)) # need to find the complement of this set where the universe is the set of all rooms
    return universe.difference(use_rooms)

@app.route("/", methods=['GET', 'POST'])
def index():
    rooms = []
    if request.method == 'POST':
        try:
            # print(request.values.get("end_time").replace(":", ""))
            rooms = find_open_rooms(request.values.get("day"),
                                         int(request.values.get("start_time").replace(":", "")), 
                                         int(request.values.get("end_time").replace(":", "")),
                                         )
        except ValueError:
            flash("Invalid input.")

    return render_template("index.html", rooms=rooms)


if __name__ == "__main__":
    # build_use_lut()
    load_use_lut()
    app.run()
    # find_open_rooms('M', 1140, 1720)
