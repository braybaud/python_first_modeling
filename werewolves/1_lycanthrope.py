import json
import logging
import random
import sys
from collections import deque

import dtk_generic_intrahost as dgi
import numpy as np

from werewolves.utils import DtkPerson, len_list_of_lists, load_constants, logger, MONTHS, Population

# Load the constants
DAYS_YEAR, HALLOWEEN_DAY, LUNAR_CYCLE, FULL_MOON_NIGHTS, MIN_WEREWOLF_SPAWN = load_constants()


class WerewolfDemo:
    def __init__(self,
                 config_filename="werewolf_config.json",
                 feed_kill_ratio=0.75,
                 enable_reporting=False):

        with open(config_filename, 'r') as infile:
            file_parameters = json.load(infile)['parameters']

        self.parameters = {'waiting_queue': file_parameters['wolf_waiting_period'],
                           'feed_death_probability': file_parameters['feed_death_probability'],
                           'enable_reporting': file_parameters['enable_reporting'],
                           'debug': file_parameters['debug']}
        self.graves = []
        self.humans = Population()
        self.time = 1
        self.werewolves = []
        self.min_age_werewolf_years = 16
        self.enable_reporting = enable_reporting
        self.feed_death_probability = feed_kill_ratio
        self.waiting_wolves = deque()

        # Take care of the waiting queue
        # Add empty elements to the queue
        for _ in range(self.parameters["waiting_queue"]):
            self.waiting_wolves.append(None)

        # If we are in debug mode -> show debug messages
        if self.parameters['debug']:
            logger.setLevel(logging.DEBUG)

        # If reporting is enabled -> start the reports
        if self.enable_reporting:
            self.report = {
                "timestep": [],
                "humans": [],
                "waiting_wolves": [],
                "hunters": [],
                "werewolves": [],
                "graves": []
            }

    def create_population(self, population_count, age_gaussian_mean=20, age_gaussian_sigma=7, probability_male=0.5):
        monte_carlo_weight = 1.0
        while len(self.humans) < population_count:
            # Choose the sex
            sex_draw = random.random()
            current_sex = 1 if sex_draw < probability_male else 0

            # Choose the age
            current_age = int(np.random.normal(loc=age_gaussian_mean, scale=age_gaussian_sigma) * DAYS_YEAR)

            # Create the human in DTK
            human = dgi.create((current_sex, current_age, monte_carlo_weight))

            # Add it to our internal population
            self.humans.append(DtkPerson(human))

    def turn_random_human_in_werewolf(self):
        # Make sure we select only old enough humans
        min_age_exposure = self.min_age_werewolf_years * DAYS_YEAR
        potential_wolves = self.humans.humans_older_than(min_age_exposure)

        # Nobody is old enough -> exit
        if len(potential_wolves) == 0:
            logger.error("No one old enough! No outbreak!")
            logger.error([h.age for h in self.humans])
            sys.exit()

        # Search for somebody old enough and born on Halloween
        potential_wolves_halloween = filter(lambda human: human.age % DAYS_YEAR == HALLOWEEN_DAY, potential_wolves)

        try:
            future_wolf = next(potential_wolves_halloween)
            logger.info("Found a new werewolf with a Halloween Birthday.")
        except StopIteration:
            logger.info("No cool birthdays, just taking someone.")
            future_wolf = potential_wolves[0]

        # Remove it from the population and add it to the wolves
        self.humans.remove(future_wolf)
        self.werewolves.append(future_wolf)
        logger.debug(f"Turned human {future_wolf.id} into a werewolf!")

    def expose_lycanthrope(self):
        dead_victims_today = []
        future_wolves = []
        if (self.time % LUNAR_CYCLE) < FULL_MOON_NIGHTS:
            logger.debug("Full moon today!")
            feeds = 0
            if self.werewolves:
                # set number of feeds if we have werewolves.
                # We want at least one feed
                feeds = round(len(self.werewolves) / 2) or 1

            logger.debug(f'With {len(self.werewolves)} werewolves, {feeds} feeds.')

            # For each feed, choose the victim
            for _ in range(feeds):
                # Choose our victim, then remove it from the population
                victim = random.choice(self.humans)
                self.humans.remove(victim)

                # Check if the victim dies
                draw = random.random()
                if draw < self.feed_death_probability:
                    # The victim died
                    dead_victims_today.append(victim)
                    logger.debug("Someone died mysteriously...")
                else:
                    # The victim survived -> it will become a wolf
                    future_wolves.append(victim)
                    logger.debug("Someone survived a bite!")

                # Quit if we have no more humans available
                if len(self.humans) <= 1:
                    logger.info("All the humans are gone!")
                    logger.info(f"Day is {self.time}")
                    self.report_step()
                    self.terminate_report()

        # Add the waiting wolves to the beginning of the list
        self.waiting_wolves.appendleft(future_wolves)

        # Add the death toll
        self.graves.append(dead_victims_today)

        # Check if we have new wolves to create
        new_wolves = self.waiting_wolves.pop()
        if new_wolves:
            for puppy in new_wolves:
                self.werewolves.append(puppy)
                logger.debug(f"Individual {puppy} is a wolf!")

    def update(self):
        # Increment the time
        self.time += 1

        # Update all humans in DTK
        for h in self.humans:
            dgi.update(h.id)

        # If its october 31st and there are no werewolves, turn somebody
        if self.time % HALLOWEEN_DAY == 0 and len(self.werewolves) == 0:
            self.turn_random_human_in_werewolf()

        # If we enable the reporting -> save the step
        if self.enable_reporting:
            self.report_step()

    def report_step(self):
        self.report["timestep"].append(self.time)
        self.report["humans"].append(len(self.humans))
        self.report["werewolves"].append(len(self.werewolves))
        self.report["waiting_wolves"].append(len_list_of_lists(self.waiting_wolves))
        self.report["graves"].append(len_list_of_lists(self.graves))

    def show_charts(self):
        import matplotlib.pyplot as plt
        plt.plot(self.report["humans"])
        plt.plot(self.report["werewolves"])
        plt.plot(self.report["waiting_wolves"])
        plt.plot(self.report["graves"])
        plt.legend(["Humans", "Werewolves", "Waiting wolves", "Deaths"])
        plt.show()

    def terminate_report(self):
        with open("werewolf_report.json", 'w') as outfile:
            json.dump(self.report, outfile, indent=4, sort_keys=True)

        self.show_charts()
        sys.exit()


if __name__ == "__main__":
    demo = WerewolfDemo(enable_reporting=True)
    demo.create_population(1000)

    # Debug info
    logger.debug("Population created\n")
    logger.debug(f'Total men: {demo.humans.men_count}\tTotal women: {demo.humans.women_count}')
    logger.debug(f'First human age: {demo.humans[0].formatted_age}\tgender:{demo.humans[0].gender.name}')
    logger.debug(f'Final human age: {demo.humans[-1].formatted_age}\tgender:{demo.humans[-1].gender.name}')
    logger.debug(f'Average age: {demo.humans.mean_age}\tStd Dev: {demo.humans.std_age}')
    print()

    # Run for 20 yeats
    for n in range(20 * DAYS_YEAR):
        # Update
        demo.update()

        # Expose
        demo.expose_lycanthrope()

        # Display a report every month
        if n != 0 and n % 30 == 0:
            logger.warning(f"{MONTHS[int(((n - 30) / 30) % 12)]} of year {int(n / 365)}")
            logger.info(f"Humans: {len(demo.humans)}\t"
                        f"Werewolves: {len(demo.werewolves)}\t"
                        f"Graveyard: {len_list_of_lists(demo.graves)}\t"
                        f"Healing: {len_list_of_lists(demo.waiting_wolves)}\n")

        # Display a message every year
        if n != 0 and n % 365 == 0:
            logger.warning("Happy new year!")
            _ = input("Ready for next year?")

        # Display a message for Halloween
        if n % 365 == HALLOWEEN_DAY:
            logger.warning("Happy Halloween!")

    demo.terminate_report()

# Move to using intrahost: Incubation for 'waiting werewolves' and infectiousness for hunger
# Move to using node demographics to create population
# Move to / consider moving to using node demographics for fertility / mortality
# Consider moving to individual properties for hunters- except IPs should not affect model behavior...
# Consider using diagnostic intervention for 'werewolf test?"
