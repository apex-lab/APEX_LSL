# ------------------------------------------------------------------------------------------------
# BUGS/things to edit/things to consider: 
# 1) code cleanliness (test lines, commenting format, redundencies, difficult to understand
#    variables,etc ...)
#  General Note: want to be addictive (think flow), not too boring and not too difficult
# 2) Incorportate Lab Streaming Layer functionality
# 3) for LSL... when you do win.flip() make sure to tie push to that
# def flip(event_name):
# win.callonflip(outlet, .... [event])
# win.flip
# fix off by one error
# Note: MAKE EVERYTHING EASY TO CHANGE LATER
# ------------------------------------------------------------------------------------------------
#import psychopy
import events, eeg, threading
from egi_pynetstation import NetStation
import pygame as pg
import sys
from random import choice, uniform
import os
from scipy.special import comb
from scipy.stats import norm
from math import sqrt, floor
from messagescreens import  *
from datetime import *
from csv import reader
from numpy import nanmean, nanstd
from warnings import filterwarnings
from pylsl import StreamInfo, StreamOutlet, StreamInlet, resolve_stream
import time

filterwarnings("ignore") #ignore warnings

# == Game Structure Variables ==
# == Attributes and relations between those attributes ==
attributes = ["targs", "speed", "dists"]
att_max = [3,3] 
scale = 1
dist_range = att_max[1] // 2
starting_targs = 2

# == how far player progresses or regresses based on performance ==
success = 1
failure = -3

# == Trial variables ==
real_time = 12 * (10 ** 5) #5000 # 12 * (10 ** 5) # time that real trials last (milliseconds)
prac_trials = 2 # number of practice trials
guide_trials = 1 # number of guide trials

# == Processing power or frames per second ==
FPS = 144

# == Defines the Objects (Balls) and their Properties ==
class MOTobj:
    def __init__(self, game, default_color):
        # -- Radius of the circle objects
        self.radius = obj_radius

        # -- Object positions attributes
        self.x, self.y = choice([n for n in range(int(boundary["left"]), int(boundary["right"]))
                                 if n not in range(x - self.radius, x + self.radius)]), \
                        choice([n for n in range(int(boundary["up"]), int(boundary["down"]))
                                 if n not in range(y - self.radius, y + self.radius)])

        # -- Velocity initialization
        self.dx, self.dy = velocity(game)

        # -- Set the circle object neutral state color
        self.color = default_color
        self.default_color = default_color

        # -- Timer attributes
        self.timer = 0
        self.flash = True

        # -- State attributes for mouse selection control
        self.state = ""
        self.isClicked = False
        self.isSelected = False
    
    def change_color(self, color):
        self.color = color

    def in_circle(self, mouse_x, mouse_y):
        # -- Return boolean value deping on mouse position, if it is in circle or not
        if sqrt(((mouse_x - self.x) ** 2) + ((mouse_y - self.y) ** 2)) < self.radius:
            return True
        else:
            return False

    def state_control(self, state):
        # -- Neutral or default state with no form of mouse selection
        if state == "neutral":
            self.color = self.default_color
            self.state = "neutral"
            self.isClicked = self.isSelected = False
        # -- Hovered state if mouse is hovering over circle object
        if state == "hovered":
            self.color = hover_col
            self.state = "hovered"
            self.isClicked = self.isSelected = False
        # -- Clicked state if mouse click DOWN while in object
        if state == "clicked":
            self.color = click_col
            self.state = "clicked"
            self.isClicked = True
            self.isSelected = False
        # -- Selected state if mouse click UP on a "clicked" object
        if state == "selected":
            self.color = select_col
            self.state = "selected"
            self.isClicked = False
            self.isSelected = True

    def draw_circle(self, display=win):
        # -- Function to draw circle onto display
        pg.draw.circle(display, self.color, (int(self.x), int(self.y)), self.radius)
        
    # add a fix for when dx/dy equals 0 (probably in brownian motion)
    def detect_collision(self, mlist):
        # -- Object positions in x and y coordinates change in velocity value
        self.x += self.dx
        self.y += self.dy
        # -- If the object reaches the window boundary, bounce back
        if self.x < boundary["left"] or self.x > boundary["right"]:
            self.dx *= -1
        if self.y < boundary["up"] or self.y > boundary["down"]:
            self.dy *= -1
        # -- If the object bounces off each other, run the Brownian motion physics
        # objects need to be from the same list, otherwise the objects
        # can pass through each other if they're from a different list
        for a in mlist:
            for b in mlist:
                if a != b:
                    if sqrt(((a.x - b.x) ** 2) + ((a.y - b.y) ** 2)) <= (a.radius + b.radius):
                        brownian_motion(a, b)

    def flash_color(self, issquare):
        # -- Function to flash color
        if self.timer == FPS:
            self.timer = 0
            self.flash = not self.flash

        self.timer += 3

        if self.flash:
            self.color = self.default_color
        else:
            if issquare:
                self.color = GREY
            else:
                self.color = GREEN

# randomly shuffles positions of balls
def shuffle_positions(mlist):
    """Shuffle the position of circles"""
    for self in mlist:
        self.x = choice([n for n in range(int(boundary["left"] + 21), int(boundary["right"] - 21))
                         if n not in range(x - self.radius, x + self.radius)])
        self.y = choice([n for n in range(int(boundary["up"] + 21), int(boundary["down"] - 21))
                         if n not in range(y - self.radius, y + self.radius)])


# checks that balls do not spawn in corner or overlap, fixes problem if it occurs
def valid_positions(mlist):
    truth_list = []
    valid_positions = False 
    while (valid_positions == False):
        for m in mlist: # iterate over all balls 
            # check if within boundaries
            if (m.x > boundary["right"]) or (m.x < boundary["left"]) or (m.y > boundary["down"]) or (m.y < boundary["up"]):
                truth_list.append(0) # if located in corner with square then invalid
            for k in mlist:
                distance = sqrt(((m.x - k.x) ** 2) + ((m.y - k.y) ** 2))
                if distance < 2 * m.radius and distance != 0:
                    truth_list.append(0) # if overlapping with another ball then invalid
        if truth_list == []: # if every ball satisfies our condition then we are fine 
            valid_positions = True
        else: #otherwise we shuffle the balls and start again
            shuffle_positions(mlist)
        truth_list = []
    
# get initial dx and dy values for balls
def velocity(game):
    speed = game["speed"]
    overall_velocity = sqrt(2 * ((speed + 2.75) ** 2))
    dx = choice([-1,1]) * uniform(0, overall_velocity)
    dy = choice([-1,1]) * sqrt((overall_velocity ** 2) - (dx ** 2))
    return dx, dy

# == returns product over elements up to and including entry n == 
def product(list, n):
    prod = 1
    for i in range(n):
        if list[len(list)- i - 1] != 0:
            prod *= list[len(list)- i - 1]
    return prod

# == Function for updating a game based on the stage ==
# -- Defines a dictionary called "game"
def update_game(stage):
    if stage < 0:
        stage = 0
    game = {"stage": stage}
    i = 0
    for att in attributes:
        prod = product(att_max, len(att_max) - i)
        if i == len(att_max):
            game[att] = stage
        elif stage >= prod:
            game[att] = stage // prod
            stage -= game[att] * prod
        else:
            game[att] = 0
        i += 1
    game["targs"] += starting_targs
    game["dists"] = game["targs"] - scale * (dist_range - game["dists"])
    if game["dists"] == 0:
        game["dists"] += 1
    return game

# == Generates a List of Objects (Balls) ==
def generate_list(game, color):
    """function to generate new list of objects"""
    target_list = []
    num_targ = game["targs"]
    for nt in range(num_targ):
        t = MOTobj(game, color)
        target_list.append(t)

    distractor_list = []
    num_dist = game["dists"] 
    for nd in range(num_dist):
        d = MOTobj(game, color)
        distractor_list.append(d)
    mlist = distractor_list + target_list # NEW NEw NEW 
    valid_positions(mlist) # NEW NEW NEW after balls for trial generated we make sure they occupy valid positions 
    return distractor_list, target_list

# == Helper Function for Delaying Game by t seconds ==
def delay(t):
    """function to stop all processes for a time"""
    pg.time.delay((t*1000))  # multiply by a thousand because the delay function takes milliseconds

# == Function for Recording User Performance ==
def record_response(participant_number, user_number, name, response_time, targs_identified, game, time_out_state, d_prime, total_time, log):
    # record the responses
    header_list = [participant_number, user_number, name, response_time, targs_identified, game["targs"], game["stage"] + 1, time_out_state, d_prime, total_time]
    # convert to string
    header_str = map(str, header_list)
    # convert to a single line, separated by commas    
    header_line = ','.join(header_str)
    header_line += '\n'
    log.write(header_line)

# == plays proper welcome messages based on gametype ==
def welcome_messages(game, gametype, high_score):
    num_targs = game["targs"]
    num_dists = game["dists"]
    total = num_targs + num_dists
    if gametype == 'guide':
        guide_screen("start", [], [], num_targs, total)
        wait_key()

        # == Fixation cross screen ==
        guide_screen("focus", [], [], num_targs, total)
        wait_key()

        # == Present cross and circles screen ==
        guide_screen("present", [], [], num_targs, total)
        wait_key()
    if gametype == 'real':
        #high_score_info(high_score)
        stage_screen(game["stage"] + 1)

# == plays proper end messages based on gametype ==
def end_messages(game, gametype, recorder):
    num_targs = game["targs"]
    num_dists = game["dists"]
    total = num_dists + num_targs
    win.fill(background_col)
    if gametype == 'real':
        message_screen("exp_finished", num_targs, total)
        pg.display.flip()
        wait_key()
        recorder.close()
    elif gametype == 'practice':
        message_screen("prac_finished", num_targs, total)
        pg.display.flip()
        wait_key()
    else:
        guide_screen("finished", [], [], num_targs, total)
        wait_key()

# == determines whether a user can take a break == 
def take_a_break(gametype, total_time):
    if gametype == 'real' and total_time >= (6 * (10 ** 5)):
        return True
    return False

# == updates the score given current score and consecutive correct trials
def update_score(score, consecutive, stage):
    return score + consecutive + floor(stage / 2)

# == function for calculating expected balls correct on a trial if user were guessing
def expected_value(game):
    targs = game["targs"]
    total = targs + game["dists"]
    EV = 0
    for i in range(targs + 1):
        numerator = comb(targs, i) * comb(total - targs, targs - i)
        denominator = comb(total, targs) #combinatorial calculation
        EV += i * (numerator / denominator)
    return EV

# == calculates d-prime value ==
def d_prime(dprimes, hit_rate, game):
    total_targs = game["targs"]
    total_balls = game["targs"] + game["dists"]

    hits = round(hit_rate[-1] * total_targs) # calculate targets correctly identified
    misses = total_targs - hits # total misses (which in MOT is equivalent to false alarms)
    farate = misses / (total_balls - total_targs)
    correct_rejections = (total_balls - total_targs) - misses # number of correct rejections

    # values for fixing extreme d primes
    half_hit = 0.5 / (hits + misses)
    half_fa = 0.5 / (misses + correct_rejections)
    # fix extreme hit rate
    hitrate = hit_rate[-1]
    if hitrate == 1:
        hitrate = 1 - half_hit
    if hitrate == 0:
        hitrate = half_hit

    # fix extreme fa rate
    if farate == 1:
        farate = 1 - half_fa
    if farate == 0:
        farate = half_fa

    # calculate z values
    z_hit = norm.ppf(hitrate)
    z_fa = norm.ppf(farate)

    dp = z_hit - z_fa # calculate d prime
    dprimes.append(dp) # add to list
    return dprimes

def update_stage(selected_targ, game, gametype, score, consecutive):
    if len(selected_targ) == game["targs"]:
        game["stage"] += success
        consecutive += 1
        score = update_score(score, consecutive, game["stage"])
    else:
        game["stage"] += failure
        consecutive = floor(consecutive / 2)
        if game["stage"] < 0:
            game["stage"] = 0
    if gametype == 'real': 
        score_screen(score) # display score
    return game, score, consecutive

# == prepares where we store data such as results and high scores ==
def prepare_files():
    participant_number = 1
    high_score = [0] * 5 # get top 5 high scores
    date_sys = str(date.today())
    user_number = user_info("User Number: ")
    name = user_info("Full Name (Please enter your name exactly [e.g. 'John Doe']): ").lower()

    if getattr(sys, 'frozen', False): 
        # The application is frozen (is an executable)
        file_path = os.path.dirname(sys.executable)
    else:
        # The application is not frozen (is not an executable)
        file_path = os.path.dirname(__file__)
    
    MOT_etc_path = os.path.join(file_path, "MOT_etc")
    try: # create a folder for results and highscores if none exists
        os.mkdir(MOT_etc_path)
    except:
        pass
    results_path = os.path.join(MOT_etc_path, "Results_MOT_exp")

    try:
        os.mkdir(results_path)
    except: # if folder for results exists then do nothing, otherwise create such a folder
        pass
    
    highscore_path = os.path.join(MOT_etc_path, "Highscore_MOT_exp")
    try:
        os.mkdir(highscore_path) 
    except: # if it does exist, then grab the high score
        with open(os.path.join(highscore_path,'highscores.csv')) as f:
            i = 0
            for line in f: # grabs top 5 high scores 
                if i == 0:
                    pass
                else:
                    if int(line) > high_score[4]:
                        high_score.append(int(line))
                        high_score.sort(reverse=True) 
                i += 1
            f.close()
    else: # if no directory exists then create one and a highscore file
        f = open(os.path.join(highscore_path,'highscores.csv'), 'w')
        f.write('High Scores\n')
        f.close()
        f = open(os.path.join(highscore_path,'highscores.csv'), 'a')
        f.write("0\n")
        f.close()

    # Creating one big csv file for all user data
    results_csv_path = os.path.join(results_path, 'results.csv')
    if not (os.path.isfile(results_csv_path)): # if it doesn't exist, then create a file
        log = open(results_csv_path, 'w')
        header = ["participant number", " user number (for Lauren)", " name", " response_time"," targets_identified"," total_targets"," level"," timed_out"," d_prime", " total_time"]
        delim = ",".join(header)
        delim += "\n"
        log.write(delim)
    else: # if exists, then get new participant number
        log = open(results_csv_path, 'r') 
        i = 0
        for row in reader(log): # grabs last participant number (last line, first entry)
            if i == 0:
                pass
            else:
                participant_number = int(row[0])
            i += 1
        participant_number += 1 # get the very next participant number
    log.close()
    log = open(results_csv_path, 'a')
    audio_path = os.path.join(file_path, 'Sound')
    return log, highscore_path, high_score, user_number, name, date_sys, audio_path, participant_number, results_path

# == Runs Real Trials (same as practice but user performance is saved) ==
def trials(game, recorder, gametype, time_or_trials, high_score, audio_path, participant_number, user_number, name, outlet, tag_dict, prediction_inlet):
    #outlet.resync()
    # == Messages to user based on gametype ==
    welcome_messages(game, gametype, high_score)
    
    # == Generates the game ==
    dt = 0
    hit_rates = []
    dprimes = []
    list_d, list_t = generate_list(game, WHITE)
    list_m = list_d + list_t
    count = 0
    break_given = False
    flash = True
    reset = False
    submitted = False
    highest_level = 0
    insufficient_selections = False # whole lot of initiating variables in this area
    timeup = False
    score = consecutive = 0 # initializes score and consecutive correct trials
    t0 = start_time = pg.time.get_ticks()
    total_time = 0
    square_time = 0

    #keeps track of which time signatures we have recorded already for a given round
    fix_record = False
    flash_record = False
    mvmt_start = False
    mvmt_stop = False


    # == Controls the "game" part of the game ==
    while True:
        num_targs = game["targs"]
        pg.time.Clock().tick_busy_loop(FPS)  # = Set FPS
        win.fill(background_col)  # - fill background with background color
        draw_boundaries()
        mx, my = pg.mouse.get_pos()  # - get x and y coord of mouse cursor on window

        selected_list = []  # - list for all selected objects
        selected_targ = []  # - list for all SELECTED TARGETS

        # == Controls responses to user input ===
        for event in pg.event.get():
            if event.type == pg.QUIT:
                #if gametype == 'real':
                square_time = draw_square(outlet, 'STOP', list_m, tag_dict)
                pg.quit()
                sys.exit()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_k and (gametype == 'guide' or gametype == 'practice'):
                    #LSL_push(outlet,'SKP') #skip
                    #square_time = draw_square(outlet, 'SKP', list_m)
                    return 'k'
                if event.key == pg.K_ESCAPE: # what is going on here
                    square_time = draw_square(outlet, 'ESCP', list_m, tag_dict)
                    outlet.push_sample(['0'])
                    if gametype == 'real':
                        #LSL_push(outlet, 'ESC') #escape/quit
                        #square_time = draw_square(outlet, 'ESCP', list_m)
                        return score, dprimes, (game["stage"] + 1), highest_level 
                    else:
                        return 'esc'
                if event.key == pg.K_SPACE and (Tani + 2 < dt <= Tans+ 2):
                    #if gametype == 'real':    
                    #LSL_push(outlet, 'SPC') #space
                    square_time = draw_square(outlet, 'SPCE', list_m, tag_dict)
                    if not reset:
                        for target in list_t:
                            if target.isSelected and not target.isClicked:
                                selected_targ.append(target)
                                selected_list.append(target)
                        for distractor in list_d:
                            if distractor.isSelected and not distractor.isClicked:
                                selected_list.append(distractor)
                        if len(selected_list) == num_targs:
                            submitted = True
                            t_keypress = pg.time.get_ticks()
                        else:
                            insufficient_selections = True
                            insuf_sel_time = pg.time.get_ticks() 
            for obj in list_m:
                if obj.in_circle(mx, my):
                    if event.type == pg.MOUSEMOTION:
                        if not obj.isClicked and not obj.isSelected:
                            obj.state_control("hovered")
                    if event.type == pg.MOUSEBUTTONDOWN:
                        if not obj.isClicked and not obj.isSelected:
                            #if gametype == 'real':   
                            square_time = draw_square(outlet, 'CLCK', list_m, tag_dict)
                            #LSL_push(outlet, 'CLK') #click object 
                            obj.state_control("clicked")
                        if not obj.isClicked and obj.isSelected:
                            #if gametype == 'real': 
                            square_time = draw_square(outlet, 'UCLK', list_m, tag_dict)
                            #LSL_push(outlet, 'UCLK') #unclick object 
                            obj.state_control("neutral")
                    if event.type == pg.MOUSEBUTTONUP:
                        if obj.isClicked and not obj.isSelected:
                            obj.state_control("selected")
                elif not obj.in_circle(mx, my):
                    if event.type == pg.MOUSEMOTION:
                        if not obj.isClicked and not obj.isSelected:
                            obj.state_control("neutral")
                    if event.type == pg.MOUSEBUTTONUP:
                        if obj.isClicked and not obj.isSelected:
                            obj.state_control("neutral")

        # == Grabs the time after each frame and total time passed in the trial ==
        t1 = pg.time.get_ticks()
        dt = (t1 - t0)/1000

        if count < time_or_trials: # need to edit because we are using time for real trials
            while (pg.time.get_ticks() - square_time < 100):
                draw_square2()
            if not reset:
                #draw_boundaries()
                if dt <= Tfix + 1:
                    if dt < (Tfix + 1) / 4:# and gametype == 'real':
                        draw_square2()
                    for targ in list_m: # hovering does not change color
                        targ.state_control("neutral")
                    pg.mouse.set_visible(False)
                    fix_record = fixation_screen(list_m, gametype, outlet, fix_record, game["stage"], tag_dict)
                elif Tfix + 1 < dt <= Tfl + 1.85:
                    for targ in list_m: # hovering does not change color
                        targ.state_control("neutral")
                    if flash == True:
                        flash, flash_record = flash_targets(list_d, list_t, flash, gametype, outlet, flash_record, tag_dict) # flash color
                        dt = Tfl + 1.95
                        flash = False
                elif Tfl + 1.85 < dt <= Tfl + 2:
                    for targ in list_m: # hovering does not change color
                        targ.state_control("neutral")
                    flash_targets(list_d, list_t, flash, gametype, outlet, flash_record, tag_dict) # reset color
                elif Tfl + 2 < dt <= Tani + 2:
                    if dt < Tfl + 2.1:# and gametype == 'real':
                        draw_square2()
                    pushed_flash_already = False
                    for targ in list_m: # hovering does not change color
                        targ.state_control("neutral")
                    mvmt_start = animate(list_d, list_t, list_m, gametype, outlet, mvmt_start, tag_dict)
                elif Tani + 2 < dt <= Tans+ 2:
                    if mvmt_stop == False:# and gametype == 'real':
                        square_time = draw_square(outlet, 'MVE1', list_m, tag_dict)
                        mvmt_stop = True
                        cur_time = pg.time.get_ticks()
                        while pg.time.get_ticks() - cur_time < 100:
                            draw_square2()

                            
                    if Tani + 2 < dt <= Tani + 2.05: # reset mouse position
                        pg.mouse.set_pos([win_width/2,win_height/2])
                    pg.mouse.set_visible(True)
                    if insufficient_selections:
                        static_draw(list_m)
                        message_screen("not_selected_enough", num_targs, num_targs + game["dists"])
                        static_draw(list_m)
                        if pg.time.get_ticks() - insuf_sel_time > 500:
                            insufficient_selections = False
                    if gametype == 'guide':
                        guide_screen("answer",list_m, selected_targ, num_targs, num_targs + game["dists"]) 
                    else: 
                        static_draw(list_m)
                    pg.display.flip()
                elif Tans + 2 < dt:
                    pg.mouse.set_visible(False)
                    timeup = True

            if submitted: # -- if the user submits answers properly
                total_time = pg.time.get_ticks() - start_time # total time in milliseconds since real trials began
                # == message screen stating performance on that trial ==
                pg.mouse.set_visible(False)
                correct_txt(len(selected_targ), len(list_t), audio_path)
                pg.mouse.set_visible(False)

                                # == Records info for the trial ==
                #if gametype == 'real':
                if len(selected_list) == len(selected_targ):# and gametype == 'real':
                    print('send correct')
                    square_time = draw_square(outlet, 'CRCT', list_m, tag_dict)
                else:
                    #if gametype == 'real':
                    print('send incorrect')
                    miss_tag = 'MS' + str(len(selected_targ)) + str(num_targs)
                    square_time = draw_square(outlet, miss_tag, list_m, tag_dict)
                hit_rates.append(len(selected_targ) / len(selected_list))
                dprimes = d_prime(dprimes, hit_rates, game)
                d_prime_string = str(dprimes[-1])[:4] # take first four elements
                if dprimes[-1] < 0 and d_prime_string[1] == '0': # reformat negative numbers to get most info out of 4 chars
                        # goal: if it is negative and begins with a 0, then remove that leading zero so we can gain an extra decimcal place
                        d_prime_string = str(dprimes[-1])[0] + str(dprimes[-1])[2] + str(dprimes[-1])[3] + str(dprimes[-1])[4]
                while len(d_prime_string) < 4:
                    d_prime_string = d_prime_string + '0'
                #try:
                    #outlet.push_sample(d_prime_string)
                #except:
                #    pass
                t_sub = ((t_keypress - t0)/1000) - animation_time
                record_response(participant_number, user_number, name, t_sub, len(selected_targ), game, False, dprimes[-1], total_time / 1000, recorder)

                # == Based on that performance, we update the stage and score ==
                game, score, consecutive = update_stage(selected_targ, game, gametype, score, consecutive)
                if game["stage"] + 1 > highest_level:
                    highest_level = game["stage"] + 1
                reset = True

            if timeup: # -- if the user runs out of time
                try:
                    outlet.push_sample([tag_dict["TMUP"]])
                except:
                    pass
                total_time = pg.time.get_ticks() - start_time # total time in milliseconds
                pg.mouse.set_visible(False)
                if gametype == 'real':
                    record_response(participant_number, user_number, name, "timed out", "NA", game, True, "NA", total_time / 1000, recorder)
                message_screen("timeup", num_targs, num_targs + game["dists"])
                delay(feedback_time)
                count -= 1
                reset = True

            if reset: # -- prepare for the next trial
                #if gametype == 'real':
                try:
                    outlet.resync() #resynchronize the clock
                except:
                    pass
                #if inter_round_record == False and gametype == 'real':
                #    square_time = draw_square(outlet, 'SCR0')
                    #LSL_push(outlet, 'SCR0') #screens start showing
                #    inter_round_record = True
                pg.mouse.set_visible(False)
                # gives user break after certain amount of time
                if take_a_break(gametype, total_time) and break_given == False:
                    break_given = True
                    user_break_screen()  

                game = update_game(game["stage"])
                list_d, list_t = generate_list(game, WHITE)
                list_m = list_d + list_t
                if gametype != 'real':
                    count += 1
                else:
                    count = total_time #* 1000
                flash = True
                submitted = timeup = insufficient_selections= reset = sound_played = False
                if gametype == 'real':
                    stage_screen(game["stage"] + 1)
                t0 = pg.time.get_ticks()
                
                # resets time signature variables for next round
                fix_record = False
                flash_record = False
                mvmt_start = False
                mvmt_stop = False
                
        else: # -- end of experiment/practice/guide
            #if gametype == 'real':
            square_time = draw_square(outlet, 'STOP', list_m, tag_dict)
                #LSL_push(outlet, 'END')
            pg.mouse.set_visible(False)
            if gametype == 'real':
                rest_screen(outlet, 2, audio_path, 'post', tag_dict)
            end_messages(game, gametype, recorder)
            if gametype == 'real':
                recorder.close()
                return score, dprimes, (game["stage"] + 1), highest_level
            else:
                return "complete" # signifies succesful completion of prac/guide trials
        

        # total gameplay time (for use in giving users a break)
        total_time = pg.time.get_ticks() - start_time # current time minus the time at which we started 

def tag_dicts():
    # still need miss and fixation tags
    tags = ['TMUP', 'STOP', 'ESCP', 'SPCE', 'CLCK', 'UCLK', 'MVE1', 'CRCT', 'STRT', 'FLSH', 'MVE0', 
    'OPN0', 'OPN1', 'OPN2', 'OPN3', 'CLS0', 'CLS1', 'CLS2', 'CLS3']
    tag_dict = {}
    rev_tag_dict = {}
    for index, tag in enumerate(tags):
        tag_dict[tag] = str(index + 2)
    length = int(tag_dict['CLS3'])

    # create fixation tags
    for i in range(1,100):
        tag = 'FX%s'%str(i)
        if len(tag) < 4:
            tag += 'X'
        tag_dict[tag] = str(length + i)
    
    length = int(tag_dict['FX99'])
    # handle miss tags
    k = 1
    for i in range(1, 10):
        for j in range(0, i):
            tag = 'MS%d%d'%(j,i)
            tag_dict[tag] = str(length + k)
            k += 1

    for tag, number_string in tag_dict.items():
        rev_tag_dict[number_string] = tag
    return tag_dict, rev_tag_dict 
# == Main Loop.  ==
def main(unified):
    mot_play_again = True
    while mot_play_again == True:
        tag_dict, rev_tag_dict = tag_dicts()
        # == Initiate pygame and collect user information ==
        #consent_screens()
        pg.init()
        pg.mixer.init()
        log, highscore_path, high_score, user_number, name, date_sys, audio_path, participant_number, results_path = prepare_files()
    
        
        # prepare lab streaming layer functionality
        # create outlet for the events
        info_events = StreamInfo('event_stream', 'events', 1, 0, 'string', str(participant_number))
        outlet = StreamOutlet(info_events)

        print('\n\n\nLooking for prediction stream...\n\n\n')
        prediction_streams = resolve_stream('name', 'prediction_stream')
        print('\n\n\nFound prediction stream named %s\n\n\n'%prediction_streams[0].name())
        prediction_inlet = StreamInlet(prediction_streams[0], recover = False)
       
        #prepare netstation functionality 
        #IP address of NetStation - CHANGE THIS TO MATCH THE IP ADDRESS OF YOUR NETSTATION
        #IP_ns = '10.10.10.42' #needs to be specified for the computer

        #IP address of amplifier (if using 300
        #series, this is the same as the IP address of
        #NetStation. If using newer series, the amplifier
        #has its own IP address)
        #IP_amp = '10.10.10.51'

        #Port configured for ECI in NetStation - CHANGE THIS IF NEEDED
        #port_ns = 55513

        #Start recording and send trigger to show this
        #try:
        #    outlet = NetStation.NetStation(IP_ns, port_ns)
        #    outlet.connect(ntp_ip = IP_amp)
        #    outlet.begin_rec()
            #send_tags(outlet) # send tags so that they will always be ordered properly
        #    outlet.send_event(event_type = 'STRT', start = 0.0)
        #except:
        #    outlet = 0
        #    send_tags(outlet)
        #start_level = choose_lvl()
        start_level = ''
        game_guide = update_game(0)
        game_prac = update_game(0)
        if start_level == '':
            game_real = update_game(0)
        else:
            game_real = update_game(int(start_level) - 1)
         # start rest screen 1 #
        rest_screen(outlet, 0, audio_path, 'pre', tag_dict)
        
        if start_level == '':
            # == Start guide ==
            key = trials(game_guide, log, 'guide', guide_trials, high_score, audio_path, participant_number, user_number, name, outlet, tag_dict, prediction_inlet)

            # == Start practice ==
            if key == 'k' or key == 'complete':
                key = trials(game_prac, log, 'practice', prac_trials, high_score, audio_path, participant_number, user_number, name, outlet, tag_dict, prediction_inlet)
        else:
            key = 'k'
        # == Start real trials, recording responses ==
        if key == 'k' or key == 'complete':
            try:
                outlet.resync()
            except:
                pass
            square_time = draw_square(outlet, 'STRT', 0, tag_dict)
            while pg.time.get_ticks() - square_time < 100:
                draw_square2()
            #LSL_push(outlet, 'real_trials_start')
            score, dprimes, last_level, highest_level = trials(game_real, log, 'real', real_time, high_score, audio_path, participant_number, user_number, name, outlet, tag_dict, prediction_inlet)
            outlet.push_sample(['0'])
        else:
            score = 0
    
        if score > high_score[4]: # update high score if applicable  
            i = 4
            while (score > high_score[i]) and (i >= 0): # calculate where on the highscore list it goes
                i = i - 1
            i += 2 # do this because we index from zero

            f = open(os.path.join(highscore_path,'highscores.csv'), 'a')
            f.writelines(str(score) + '\n')
            f.close()
            #new_high_score(score, i)
        else:
            pass
            #final_score(score)

        summary_csv_path = os.path.join(results_path, 'summary.csv')
        if not (os.path.isfile(summary_csv_path)): # if it doesn't exist, then create a file
            f = open(summary_csv_path, 'w')
            header = ["participant number", " user_number (for Lauren)", " name", " dprime_avg", " dprime_std", " highest_level_obtained", " last_level", " score"]
            delim = ",".join(header)
            delim += "\n"
            f.write(delim)
            f.close()
        f = open(summary_csv_path, 'a')
            # record the responses
        try:
            header_list = [participant_number, user_number, name, nanmean(dprimes), nanstd(dprimes), highest_level, last_level, score]
        except:
            header_list = [participant_number, user_number, name, "NaN", "NaN", "NaN", "NaN", "NaN"]
        # convert to string
        header_str = map(str, header_list)
        # convert to a single line, separated by commas    
        header_line = ','.join(header_str)
        header_line += '\n'
        f.write(header_line)
        f.close()

        # allow user to play again without rerunning program
        pg.mixer.quit()
        mot_play_again = play_again_exp()
        if mot_play_again == True:
            if unified == True:
                return True
        else:
            if unified == True:
                return False
            else:
                pg.quit()
                sys.exit()

if __name__ == "__main__":
    main(False)