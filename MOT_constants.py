import math
from random import randint, choice
import time 
from screeninfo import get_monitors




# == Path For Storing Trial Results. ==
save_path = 'C:\\Users\\Administrator\\psychexperiment\\multiple-object-tracking-paradigm\\results\\'
"""
Define the object class attributes
"""
obj_radius: int = 35  # size of balls in pixels

"""
Define the times and durations in SECONDS
"""
fix_draw_time = Tfix = 1.5 # time to present fixation cross and objects

flash_time = Tfl = fix_draw_time + 1  # time for targets to flash

animation_time = Tani = flash_time + 4.5  # time for objects to move around in seconds

answer_time = Tans = animation_time + 60  # time limit to make answer

feedback_time = 1


"""
Define the project display window
"""
title = "Multiple Object Tracking Experiment"

# getting window size (will handle dpi later)
winfo = [] #stores monitor info as a string so we can extract window size info
for m in get_monitors():
    winfo.append(m)

win_width = m.width
win_height = m.height  # pixels; width of screen
win_dimension = (win_width, win_height)

"""
Define instruction texts.
"""
def start_text(num_targ, total):
    return "You will first see a cross at the center of the screen. Please focus your gaze to that cross.\n\n" \
    "There will be " + str(total) + " circles appearing on the screen, " + str(num_targ) + " of them will flash in GREEN.\n" \
    "The cross will disappear, and all circles will start to move. Keep track of those " + str(num_targ) + \
    " flashed circles.\n\nWhen the circles stop moving, select which circles you've been tracking by clicking " \
    "them.\nWhen you have made your selection, press the SPACEBAR to submit your selection.\n\n" \
    "If you need to stop, let the experimenter know or press ESCAPE if you are in the middle of a trial. \n\n" \
    "Please remember to focus your eyes on the cross.\n" \
    "Press F to start when you are ready."

def start_text_nback():
    return "Welcome to the n-back task. \n\n" \
    "In this experiment you will see a sequence of letters.\n\n" \
    "Your goal is to remember these letters and identify when a letter repeats itself after n number of letters. For example, if n = 1, then" \
    " you are performing a 1-back task and you must remember when the same letter occurs twice in a row. For a 2-back you must identify" \
    " when a pattern repeats with some other pattern in between. If 'X','Y','Z' are three letters, then a 1-back is a sequence such as '...X,X...'"\
    ", a 2-back is a sequence such as '...X, Y, X...' and a 3-back would be '...X, Y, Z, X...' .\n\n" \
    "Press the SPACEBAR when you see one of these \'n-back\' targets.\n" \
    "Remember: In a 1-back task, you only click the spacebar for 1-backs, in a 2-back you only click the spacebar for 2-backs,... \n\n"\
    "Press F to start when you are ready.\n\nIf you need to stop, let the experimenter know or press ESCAPE if you are in the middle of a trial. "\
    "Furthermore, you may press \"k\" to skip through the practice trials once the balls have been displayed."
    

fix_text = "First, you will see this cross. Please focus your gaze here. \nPress F to continue."

practice_text = "You will now practice with a 1-back task and a 2-back task. \n\nPress F to continue."
def input_text():
    return "Please enter the requested information. Then press Enter or Return to continue. Press ESC to exit or inform the observer of your decision. \n\n"

def present_text(num_targ, total): 
    return "Now, " + str(total) + " circles will appear randomly around the screen. " + str(num_targ) + " random " \
    "circles will flash briefly. Remember which circles flashed. The cross will disappear, and all circles " \
    "will start moving when the flashing stops.\n\nPress F to continue."\
    

submit_ans_txt = "When the circles stop moving, select the circles that you've been tracking.\n" \
                 "You will have {:d} seconds to make your choice.\n\n" \
                 "Press SPACEBAR to submit your answer.".format(int(answer_time-animation_time))

prac_finished_txt = "The practice is now over.\n\nPress the F when you are ready to continue to the real " \
                    "experiment.\nRemember to keep track of the targets and submit your result by " \
                    "pressing the SPACEBAR.\n\nBe as quick and accurate as you can!\n\n" \
                    "Press F to continue."

experim_fin_txt = "The experiment is now over; let the experimenter know.\n\nThank you for participating!" \
                  "\n\nPress F to exit."

guide_fin_txt = "The guide is now complete, and you will move to practice rounds, where you will go through the " \
                "experiment in normal order, but your answers will not be recorded.\n\nAfter the practice is finished, " \
                "you will move to the real experiments where your responses will be recorded.\n\n" \
                "Press F to move to the practice rounds."

guide_fin_txt_nback = "The guide is now complete.\n\n" \
                "Press F to move to the real rounds."

guide_submit_txt = "You've selected {:d} targets correctly."

guide_timeup_txt = "Time is up! You will now repeat the trial."

def high_scores_info_txt(high_scores):
    return "Current High Scores \n\n 1. " + str(high_scores[0]) + "\n\n 2. " + str(high_scores[1]) + "\n\n 3. " \
         + str(high_scores[2]) + "\n\n 4. " + str(high_scores[3]) + "\n\n 5. " + str(high_scores[4])


def stage_txt(game):
        return " Stage " + str(game["stage"]) 

# == Font size ==
extra_large_font = 120
large_font = 72
med_font = 42
small_font = 12

"""
Define some colours.
"""
# == Greyscale ==
BLACK = [0, 0, 0]
WHITE = [255, 255, 255]
GREY = [128, 128, 128]
SLATEGREY = [112, 128, 144]
DARKSLATEGREY = [47, 79, 79]
default_color = WHITE
# == Yellows ==
YELLOW = [255, 255, 0]
OLIVE = [128,128,0]
DARKKHAKI = [189,183,107]

# == Greens ==
GREEN = [0, 128, 0]
GREENYELLOW = [173, 255, 47]

RED = [255, 50, 50]

"""
Generate random x and y coordinates within the window boundary
"""
boundary_size: int = 30 # how large the boundary is
boundary_location = ['up', 'down', 'left', 'right']
boundary_coord = [obj_radius + boundary_size, (win_height - (obj_radius + boundary_size)), obj_radius + boundary_size, (win_width - (obj_radius + boundary_size))]
boundary = dict(zip(boundary_location, boundary_coord))

listX, listY = [], []
rangeX, rangeY = range(boundary['left'], boundary['right']), range(boundary['up'], boundary['down'])

"""
Define session information for recording purposes
"""
session_info = {'Observer': 'Type observer initials', 'Participant': 'Type participant ID'}
date_string = time.strftime("%b_%d_%H%M", time.localtime())  # add the current time


def brownian_motion(C1, C2):
    """ ===== FUNCTION TO CALCULATE BROWNIAN MOTION ===== """
    c1_spd = math.sqrt((C1.dx ** 2) + (C1.dy ** 2))
    diff_x = -(C1.x - C2.x)
    diff_y = -(C1.y - C2.y)
    vel_x = 0
    vel_y = 0
    if diff_x > 0:
        if diff_y > 0:
            angle = math.degrees(math.atan(diff_y / diff_x))
            vel_x = -c1_spd * math.cos(math.radians(angle))
            vel_y = -c1_spd * math.sin(math.radians(angle))
        elif diff_y < 0:
            angle = math.degrees(math.atan(diff_y / diff_x))
            vel_x = -c1_spd * math.cos(math.radians(angle))
            vel_y = -c1_spd * math.sin(math.radians(angle))
    elif diff_x < 0:
        if diff_y > 0:
            angle = 180 + math.degrees(math.atan(diff_y / diff_x))
            vel_x = -c1_spd * math.cos(math.radians(angle))
            vel_y = -c1_spd * math.sin(math.radians(angle))
        elif diff_y < 0:
            angle = -180 + math.degrees(math.atan(diff_y / diff_x))
            vel_x = -c1_spd * math.cos(math.radians(angle))
            vel_y = -c1_spd * math.sin(math.radians(angle))
    elif diff_x == 0:
        if diff_y > 0:
            angle = -90
        else:
            angle = 90
        vel_x = c1_spd * math.cos(math.radians(angle))
        vel_y = c1_spd * math.sin(math.radians(angle))
    elif diff_y == 0:
        if diff_x < 0:
            angle = 0
        else:
            angle = 180
        vel_x = c1_spd * math.cos(math.radians(angle))
        vel_y = c1_spd * math.sin(math.radians(angle))
    if vel_x == 0 and vel_y == 0:
        vel_x, vel_y = 1.5, 1.5
    C1.dx = vel_x
    C1.dy = vel_y