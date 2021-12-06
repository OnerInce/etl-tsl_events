import os
import re
import ssl
from operator import itemgetter

import requests
import urllib3
from bs4 import BeautifulSoup
from smart_open import open

ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MAIN_PAGE = "https://tff.org/default.aspx?pageID=545"
FIRST_VALID_SEASON_URL = "http://www.tff.org/default.aspx?pageID=561"


class Match:
    def __init__(self, url_match):
        self.match_url = url_match
        self.match_soup = BeautifulSoup(requests.get(url_match, timeout=5, verify=ssl.CERT_NONE, headers={"User-agent":
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"}).content,
                                        "html.parser")
        self.home_team = None
        self.away_team = None
        self.referee = None
        self.day = None
        self.time = None
        self.goals = None
        self.subs = None
        self.red_cards = None

        self.events_array = None

    def parse_match_data(self):
        self.parse_teams()
        self.parse_referee()
        self.parse_goals()
        self.parse_date()
        self.parse_subs()
        self.parse_red_cards()
        self.create_json()

    def parse_teams(self):
        teams_tag = self.match_soup.find_all('a', {'id': re.compile(r'Takim.$')})
        team_one, team_two = teams_tag[0].text, teams_tag[1].text

        self.home_team = team_one.strip()
        self.away_team = team_two.strip()

    def parse_referee(self):
        ref_tag = self.match_soup.find('a', {'id': re.compile(r'Hakem')})
        ref_name = ref_tag.text[:-7]

        self.referee = ref_name

    def parse_date(self):
        date_tag = self.match_soup.find('span', id=lambda x: x and "Tarih" in x).text
        date_splitted = date_tag.split("-")
        try:
            date, time = date_splitted[0], date_splitted[1]
        except IndexError:
            date = date_splitted[0]
            time = 'Yok'

        self.day = date
        self.time = time

    def parse_goals(self):
        all_goals = []

        goals = self.match_soup.findAll('a', id=lambda x: x and "Goller" in x)

        for i in goals:
            goal_info = i.text
            team_id = re.search(r'Takim.', str(i)).group(0)[-1]
            splitted_goal_info = goal_info.split(",")
            scorer = splitted_goal_info[0]
            scored_with = goal_info[-2]

            try:
                goal_minute = int(splitted_goal_info[1].split(".")[0])
            except ValueError:  # if goal scored in extra minutes
                splitted_by_plus = splitted_goal_info[1].split(".")[0].split("+")
                goal_minute = int(splitted_by_plus[0]) + int(splitted_by_plus[1])

            if int(team_id) == 1:
                goal_element = ['home', scorer, goal_minute, scored_with]
            else:
                goal_element = ['away', scorer, goal_minute, scored_with]

            all_goals.append(goal_element)

        self.goals = sorted(all_goals, key=itemgetter(2))

    def parse_subs(self):
        team_one_out, team_two_out = [], []
        team_one_in, team_two_in = [], []

        subs_in_tags = self.match_soup.find_all(['a', "span"], {'id': re.compile(r'Takim._rptCikanlar')})
        team_id = 1

        for e, i in enumerate(subs_in_tags):
            if e == 0:
                continue
            if i.text == "Oyundan Çıkanlar":
                team_id = 2
                continue
            if team_id == 1:
                team_one_out.append(i.text)
            else:
                team_two_out.append(i.text)

        subs_out_tags = self.match_soup.find_all(['a', "span"], {'id': re.compile(r'Takim._rptGirenler')})
        team_id = 1

        for e, i in enumerate(subs_out_tags):
            if e == 0:
                continue
            if i.text == "Oyuna Girenler":
                team_id = 2
                continue

            if team_id == 1:
                team_one_in.append(i.text)
            else:
                team_two_in.append(i.text)

        team_one_all = [team_one_in, team_one_out]
        team_two_all = [team_two_in, team_two_out]

        all_subs = [team_one_all, team_two_all]
        self.subs = all_subs

    def parse_red_cards(self):
        team_one_red, team_two_red = [], []
        red_card_tags = self.match_soup.find_all('img', {'alt': ["Çift Sarı Kart", "Kırmızı Kart"]})

        for i in red_card_tags:
            team_id = re.search(r'Takim.', str(i)).group(0)[-1]
            name_minute = i.text.strip()
            name_minute_splitted = name_minute.split("\n")

            # Discard cards seen after the match

            if name_minute_splitted[-1] == "MS":
                continue

            if int(team_id) == 1:
                team_one_red.extend(name_minute_splitted)
            else:
                team_two_red.extend(name_minute_splitted)

            all_red_cards = [team_one_red, team_two_red]
            self.red_cards = all_red_cards

    def create_json(self):
        constant_info = {
            'match_start_date': self.day.strip(),
            'match_start_time': self.time.strip(),
            'home_team': self.home_team,
            'away_team': self.away_team,
            'referee': self.referee
        }

        events = []

        if len(self.goals) > 0:
            home_score, away_score = 0, 0

            for goal in self.goals:
                dict_merge = {}

                if goal[0] == 'home':
                    home_score += 1
                else:
                    away_score += 1

                event_json = {'type': 'goal', 'scoring_team': goal[0], 'scorer': goal[1], 'event_minute': goal[2],
                              'scored_with': goal[3], 'current_home_score': home_score,
                              'current_away_score': away_score}

                dict_merge.update(event_json)
                dict_merge.update(constant_info)

                events.append(dict_merge)

        sub_time = None

        if self.subs is not None:

            for home_sub_in, home_sub_out in zip(reversed(self.subs[0][0]), reversed(self.subs[0][1])):
                if ".dk" in home_sub_in:
                    sub_time = home_sub_in.split(".")[0]
                    continue

                dict_merge = {}

                event_json = {'type': 'home_sub', 'event_minute': sub_time, 'sub_in': home_sub_in,
                              'sub_out': home_sub_out}

                dict_merge.update(event_json)
                dict_merge.update(constant_info)

                events.append(dict_merge)

            for away_sub_in, away_sub_out in zip(reversed(self.subs[1][0]), reversed(self.subs[1][1])):
                if ".dk" in away_sub_in:
                    sub_time = away_sub_in.split(".")[0]
                    continue

                dict_merge = {}

                event_json = {'type': 'away_sub', 'event_minute': sub_time, 'sub_in': away_sub_in,
                              'sub_out': away_sub_out}

                dict_merge.update(event_json)
                dict_merge.update(constant_info)

                events.append(dict_merge)

        if self.red_cards is not None:

            card_time = None

            for home_red in reversed(self.red_cards[0]):
                if ".dk" in home_red:
                    card_time = home_red.split(".")[0]
                    continue

                dict_merge = {}

                event_json = {'type': 'home_red', 'event_minute': card_time, 'info': home_red}

                dict_merge.update(event_json)
                dict_merge.update(constant_info)

                events.append(dict_merge)

            for away_red in reversed(self.red_cards[1]):
                if ".dk" in away_red:
                    card_time = away_red.split(".")[0]
                    continue

                dict_merge = {}

                event_json = {'type': 'away_red', 'event_minute': card_time, 'info': away_red}

                dict_merge.update(event_json)
                dict_merge.update(constant_info)

                events.append(dict_merge)

        self.events_array = events

    def __str__(self):
        return_str = f"""
        'Match date: ' {self.day}
        'Match time: ' {self.time}
        'Home team: ' {self.home_team}
        'Away team: ' {self.away_team}
        'Referee: ' {self.referee}
        'Home team goals: ' {self.goals[0]}
        'Away team goals: ' {self.goals[1]}
        'Home team subs: ' {self.subs[0]}
        'Away team subs: ' {self.subs[1]}
        'Home team red cards: ' {self.red_cards[0]}
        'Away team red cards: ' {self.red_cards[1]}
        """.strip()

        return return_str


def create_match_obj_list():
    """
    read match_urls file from s3 and create match objects
    """

    with open(f"s3://{os.environ['BUCKET_NAME']}/match_urls.txt") as f:
        content = f.readlines()

    all_matches = [x.strip() for x in content]

    match_obj_list = []
    for match_url in all_matches:
        print("Parsing match url", match_url)
        try:
            match = Match(match_url)
            match.parse_match_data()
            match_obj_list.append(match)
        except Exception as e:
            print(str(e))
            continue

    return match_obj_list
