import configparser
import json
import logging
import sys
from collections import Iterable
from enum import Enum

import dtk_generic_intrahost as dgi
import numpy as np

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November",
          "December"]


class bcolors:
    """
    Colors for the console
    """
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


class CustomConsoleFormatter(logging.Formatter):
    """
    Modify the way DEBUG messages are displayed.
    """

    def format(self, record):
        if record.levelno == logging.DEBUG:
            return f'{bcolors.BLUE}[DEBUG] {record.msg}{bcolors.ENDC}'
        elif record.levelno == logging.WARNING:
            return f'{bcolors.WARNING}{record.msg}{bcolors.ENDC}'
        elif record.levelno >= logging.ERROR:
            return f'{bcolors.FAIL}[ERROR] {record.msg}{bcolors.ENDC}'
        return record.msg


# Configure logging
logger = logging.getLogger('Lycanthrope')

# Console handler
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(CustomConsoleFormatter())
logger.addHandler(ch)
logger.setLevel(logging.INFO)


def load_constants():
    """
    Load all the constants coming from globals.ini and return them
    """
    # Load the constants
    config = configparser.ConfigParser()
    config.read('globals.ini')
    return int(config["DEFAULT"]["DAYS_YEAR"]), \
           int(config["DEFAULT"]["HALLOWEEN_DAY"]), \
           int(config["DEFAULT"]["LUNAR_CYCLE"]), \
           int(config["DEFAULT"]["FULL_MOON_NIGHTS"]), \
           int(config["DEFAULT"]["MIN_WEREWOLF_SPAWN"])


def len_list_of_lists(iterable: Iterable) -> int:
    """
    Return the count of elements in a list of lists
    :param iterable: List of lists
    :return: Length of list of lists
    """
    return sum(len(s) for s in iterable if s)


class Gender(Enum):
    male = 1
    female = 0


class State(Enum):
    healthy = 0
    incubating = 1
    infected = 2
    dead = 3


class DtkPerson:
    """
    Represent a DTK person
    id: id in DTK
    """

    def __init__(self, person_id: int):
        self.id = person_id
        individual_info = json.loads(dgi.serialize(self.id))["individual"]
        self.gender = Gender(individual_info["m_gender"])
        self.age = individual_info["m_age"]
        self.mcw = individual_info["m_mc_weight"]
        self.state = State.healthy

    @property
    def formatted_age(self):
        """
        Returns a string representing the age
        """
        year = int(self.age / 365)
        months = int((self.age % 365) / 30)
        days = (self.age % 365) % 30
        return f"{year} years, {months} months, {int(days)} days"

    def __repr__(self):
        return f"<Individual {self.gender} #{self.id} - age: {self.age}>"


class Population(list):
    """
    Represents a population of individuals (DTKPerson)
    """

    def humans_older_than(self, age: int, state: State = None):
        """
        Returns a list of humans older than a given age.
        Optionally pass a state to also filter by state
        :param age: Minimum age (non inclusive)
        :param state: State
        :return: List of filtered individuals
        """
        if state:
            return list(filter(lambda human: human.age > age, self.get_humans_with_state(state)))
        return list(filter(lambda human: human.age > age, self))

    @property
    def men_count(self):
        """
        Count of males in the population
        """
        return sum(human.gender == Gender.male for human in self)

    @property
    def women_count(self):
        """
        Count of females in the population
        """
        return sum(human.gender == Gender.female for human in self)

    @property
    def mean_age(self):
        """
        Mean age of the population
        """
        return np.mean([human.age for human in self])

    @property
    def std_age(self):
        """
        Standard deviation of ages in the population
        """
        return np.std([human.age for human in self])

    def count_state(self, state: State):
        """
        How many individuals with the given state
        """
        return sum(human.state == state for human in self)

    def get_humans_with_state(self, state: State):
        """
        Get individuals with a given state
        """
        return list(filter(lambda human: human.state == state, self))
