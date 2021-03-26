import requests
from bs4 import BeautifulSoup
import re

MAIN_PAGE = "https://tff.org/default.aspx?pageID=545"
LAST_VALID_SEASON_URL = "http://www.tff.org/default.aspx?pageID=561"


class Match:
    def __init__(self, url_match):
        self.match_url = url_match
        self.match_soup = BeautifulSoup(requests.get(url_match).content, "html.parser")
        self.home_team = None
        self.away_team = None
        self.referee = None
        self.day = None
        self.time = None
        self.goals = None
        self.subs = None
        self.red_cards = None

    def parse_match_data(self):
        self.parse_teams()
        self.parse_referee()
        self.parse_goals()
        self.parse_date()
        self.parse_subs()
        self.parse_red_cards()
    
    def parse_teams(self):
        teams_tag = self.match_soup.find_all('a', {'id': re.compile(r'Takim.$')})
        team_one, team_two = teams_tag[0].text, teams_tag[1].text

        self.home_team = team_one
        self.away_team = team_two

    def parse_referee(self):
        ref_tag = self.match_soup.find('a', {'id': re.compile(r'Hakem')})
        ref_name = ref_tag.text[:-7]

        self.referee = ref_name

    def parse_date(self):
        date_tag = self.match_soup.find('span', id=lambda x: x and "Tarih" in x).text
        date_splitted = date_tag.split("-")
        date, time = date_splitted[0], date_splitted[1]

        self.day = date
        self.time = time

    def parse_goals(self):
        goals = self.match_soup.findAll('a', id=lambda x: x and "Goller" in x)
        team_one_goals, team_two_goals = [], []

        for i in goals:
            team_id = re.search(r'Takim.', str(i)).group(0)[-1]
            if int(team_id) == 1:
                team_one_goals.append(i.text)
            else:
                team_two_goals.append(i.text)

        all_goals = [team_one_goals, team_two_goals]
        self.goals = all_goals

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

    def __str__(self):
        return_str = f"""
        'Maç tarihi: ' {self.day}
        'Maç saati: ' {self.time}
        'Ev Sahibi: ' {self.home_team}
        'Deplasman: ' {self.away_team}
        'Hakem: ' {self.referee}
        'Ev Sahibi Goller: ' {self.goals[0]}
        'Deplasman Goller: ' {self.goals[1]}
        'Ev Sahibi Değişiklikler: ' {self.subs[0]}
        'Deplasman Değişiklikler: ' {self.subs[1]}
        'Ev Sahibi Kırmızı Kartlar: ' {self.red_cards[0]}
        'Deplasman Kırmızı Kartlar: ' {self.red_cards[1]}
        """

        return return_str


def get_valid_season_urls():

    content = requests.get(MAIN_PAGE).content
    soup = BeautifulSoup(content, "html.parser")

    seasons_td = soup.find_all("td", attrs={"class": "alanSuperLig"})
    seasons_td = [x for x in seasons_td if "Şampiyonlukları" in x.text][0]

    table_element = seasons_td.findParents('table')[0]

    seasons = table_element.findChildren("a")
    seasons = [x["href"] for x in seasons]
    last_valid_season_index = seasons.index(LAST_VALID_SEASON_URL)

    valid_seasons = []
    for e, season in enumerate(seasons):
        if e < last_valid_season_index:
            continue
        valid_seasons.append(season)

    return valid_seasons


def get_all_weeks_urls(season_url):
    content = requests.get(season_url).content
    soup = BeautifulSoup(content, "html.parser")
    all_weeks = soup.find_all("td", attrs={"class": ["haftaNoOn", "haftaNoOff"]})
    all_weeks = ["http://www.tff.org/" + x.findChild("a")['href'] for x in all_weeks]

    return all_weeks


def get_single_weeks_matches(week_url):

    content = requests.get(week_url).content
    soup = BeautifulSoup(content, "html.parser")

    weeks_matches_anchor = soup.findAll('a', id=lambda x: x and "HaftaninMaclari" in x)
    weeks_matches_urls = ["http://www.tff.org/" + x["href"] for x in weeks_matches_anchor if "kulup" not in x["href"]]

    weeks_matches_urls = list(set(weeks_matches_urls))

    return weeks_matches_urls


match_url = "https://www.tff.org/Default.aspx?pageId=29&macId=219182"

match = Match(match_url)
match.parse_match_data()
