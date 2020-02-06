# Move to reading constants out of a config file

import dtk_generic_intrahost as dgi
from collections import deque

DAYS_YEAR = 365
HALLOWEEN_DAY = 304
LUNAR_CYCLE = 28
FULL_MOON_NIGHTS = 2
MIN_WEREWOLF_SPAWN = 17
import random
import sys
import json

import numpy as np


class WerewolfDemo(object):
    class WaitingQueue(list):
        def __init__(self, wait_length_days=40):
            my_queue = []
            for x in range(wait_length_days):
                my_queue.append([])
                pass
            self.queue = my_queue
            pass


        def enqueue(self, person_list):
            self.queue.append(person_list)
            pass

        def dequeue(self):
            # TODO: handle zero length queue
            return_list = self.queue[0]
            self.queue.remove(return_list)
            return return_list

        def count_queue(self):
            total = 0
            for x in self.queue:
                total += len(x)
                pass
            return total

    def __init__(self,
                 config_filename="werewolf_config.json",
                 feed_kill_ratio=0.75,
                 enable_reporting=False,
                 debug=False):
        with open(config_filename) as infile:
            file_parameters = json.load(infile)['parameters']
        params = {}
        params['waiting_queue'] = file_parameters['wolf_waiting_period']
        params['feed_death_probability'] = file_parameters['feed_death_probability']
        params['enable_reporting'] = file_parameters['enable_reporting']
        params['debug'] = file_parameters['debug']
        self.parameters = params
        self.humans = []
        self.time = 1
        self.wounded_count = 0
        self.death_queue = deque([])
        self.werewolves = []
        self.waiting_wolves = self.WaitingQueue(params['waiting_queue'])
        self.graves = []
        self.feed_death_probability = feed_kill_ratio
        self.debug = self.parameters['debug']
        self.min_age_werewolf_years = 16
        self.enable_reporting = enable_reporting
        if self.enable_reporting:
            self.report = {
                "timestep":[],
                "humans": [],
                "waiting_wolves": [],
                "hunters": [],
                "werewolves": [],
                "graves": []
            }

    def create_person_callback(self, mcw, age, gender):
        self.humans.append(dgi.create((gender, age, mcw)))

    def create_population(self, population_count, age_gaussian_mean=20, age_gaussian_sigma=7, probability_male=0.5):
        total_population = 0
        monte_carlo_weight = 1.0
        while total_population < population_count:
            sex_draw = random.random()
            current_sex = 0
            if sex_draw < probability_male:
                current_sex = 1
                pass
            current_age = int(np.random.normal(loc=age_gaussian_mean, scale=age_gaussian_sigma) * DAYS_YEAR)
            human = dgi.create((current_sex, current_age, monte_carlo_weight))
            self.humans.append(human)
            total_population += 1

    def expose_lycanthrope(self):
        deaths_today = 0
        future_wolves = []
        if ((self.time % LUNAR_CYCLE) < FULL_MOON_NIGHTS):
            feeds = 0
            if self.werewolves:
                # set number of feeds
                feeds = round(len(self.werewolves) / 2)
                if feeds == 0:
                    feeds +=1
                pass
            if self.debug:
                print(f'With {len(self.werewolves)} werewolves, {feeds} feeds.')
            for n in range(feeds):
                victim = random.choice(self.humans)
                self.humans.remove(victim)
                draw = random.random()
                if draw < self.feed_death_probability:
                    self.graves.append(victim)
                    if self.debug:
                        print("Someone died mysteriously...")
                    deaths_today += 1
                else:
                    future_wolves.append(victim)
                    if self.debug:
                        print("Someone survived a bite!")
                if len(self.humans) <= 1:
                    print("All the humans are gone!")
                    print(f"Day is {self.time}")
                    self.report_step()
                    self.terminate_report()
                    pass
                pass
        self.waiting_wolves.enqueue(future_wolves)
        self.death_queue.append(deaths_today)
        return self.waiting_wolves.dequeue()

    def update(self):
        self.time += 1
        for h in self.humans:
            dgi.update(h)
        if self.time % HALLOWEEN_DAY == 0: # It is october 31
            if len(self.werewolves) == 0: # and there are no werewolves
                found_one = False
                possible_humans = len(self.humans)
                ages = []
                min_age_exposure = self.min_age_werewolf_years * DAYS_YEAR
                while not found_one and possible_humans > 0:
                    for h in self.humans:
                        possible_humans -=1
                        age = dgi.get_age(h)
                        ages.append(age)
                        if age > min_age_exposure:
                            if age % DAYS_YEAR == HALLOWEEN_DAY:
                                self.humans.remove(h)
                                self.werewolves.append(h)
                                found_one = True
                                break
                if found_one:
                    print("Found a new werewolf with a Halloween Birthday.")
                else:
                    print("No cool birthdays, just taking someone.")
                    future_wolf = None
                    for h in self.humans:
                        age = dgi.get_age(h)
                        if not future_wolf and age > min_age_exposure:
                            self.humans.remove(h)
                            self.werewolves.append(h)
                            future_wolf = h
                    if future_wolf:
                        print("Found someone old enough.")
                    else:
                        print("No one old enough! No outbreak!")
                        print(ages)
                        sys.exit()
        if self.enable_reporting:
            self.report_step()

    def report_step(self):
        self.report["timestep"].append(self.time)
        self.report["humans"].append(len(self.humans))
        self.report["werewolves"].append(len(self.werewolves))
        self.report["waiting_wolves"].append(self.waiting_wolves.count_queue())
        self.report["graves"].append(len(self.graves))

    def terminate_report(self):
        with open("werewolf_report.json",'w') as outfile:
            import json
            json.dump(self.report, outfile, indent=4, sort_keys=True)
        sys.exit()

class DtkPerson(object):
    def __init__(self, person_id:int):
        self.id = person_id
        pass

    def serialize_me(self):
        my_j = json.loads(dgi.serialize(self.id))
        self.individual_json = my_j["individual"]

    def get_age(self):
        self.serialize_me()
        return self.individual_json["m_age"]

    def is_male(self):
        self.serialize_me()
        gender_int = self.individual_json["m_gender"]
        if gender_int == 1:
            return True
        else:
            return False

    def get_mcw(self):
        self.serialize_me()
        return self.individual_json["m_mc_weight"]
    pass


if __name__ == "__main__":
    demo = WerewolfDemo(debug=False, enable_reporting=True)
    demo.create_population(1000)
    if demo.debug:
        print("Population created\n")
        men = 0
        women = 0
        ages = []
        for h in demo.humans:
            alex = DtkPerson(h)
            if alex.is_male():
                men += 1
            else:
                women += 1
                pass
            ages.append(alex.get_age())
            pass
        print(f'Total men: {men}\tTotal women: {women}')
        adam = DtkPerson(demo.humans[0])
        galactus = DtkPerson(demo.humans[-1])
        print(f'First human age: {adam.get_age()}\tmale:{adam.is_male()}')
        print(f'Final human age: {galactus.get_age()}\tmale:{galactus.is_male()}')
        mean = np.mean(ages)
        std_dev = np.std(ages)
        print(f'Average age: {mean}\tStd Dev: {std_dev}')
        sys.exit(0)
    for n in range(20*DAYS_YEAR):
        demo.update()
        new_wolves = demo.expose_lycanthrope()
        for puppy in new_wolves:
            demo.werewolves.append(puppy)
            if demo.debug:
                print(f"Individual {puppy} is a wolf!")
        if n % 30 == 0:
            print(f"Humans: {len(demo.humans)}\tWerewolves: {len(demo.werewolves)}\tGraveyard: {len(demo.graves)}\tHealing: {demo.waiting_wolves.count_queue()}\n")
        if n % 365 == 0:
            print("Happy new year!")
            foo = input("Ready for next year?")
        if n % 365 == HALLOWEEN_DAY:
            print("Happy Halloween!")
    demo.terminate_report()

# Move to using intrahost: Incubation for 'waiting werewolves' and infectiousness for hunger
# Move to using node demographics to create population
# Move to / consider moving to using node demographics for fertility / mortality
# Consider moving to individual properties for hunters- except IPs should not affect model behavior...
# Consider using diagnostic intervention for 'werewolf test?"







