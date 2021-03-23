import requests
from bs4 import BeautifulSoup
import re

MAIN_PAGE = "https://tff.org/default.aspx?pageID=545"
LAST_VALID_SEASON_URL = "http://www.tff.org/default.aspx?pageID=561"


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


match_url = "https://www.tff.org/Default.aspx?pageId=397&macId=61972"

content = requests.get(match_url).content
soup = BeautifulSoup(content, "html.parser")

# Golleri al

goals = soup.findAll('a', id=lambda x: x and "Goller" in x)
team_one_goals = []
team_two_goals = []

for i in goals:
    team_name_id = re.search(r'Takim.', str(i))
    team_id = team_name_id.group(0)[-1]
    if int(team_id) == 1:
        team_one_goals.append(i.text)
    else:
        team_two_goals.append(i.text)

print(team_one_goals)
print(team_two_goals)

# Maç tarihini ve saatini al

date_tag = soup.find('span', id=lambda x: x and "Tarih" in x).text
date_splitted = date_tag.split("-")

date, time = date_tag[0], date_tag[1]

# Takımları al

teams_tag = soup.find_all('a', {'id': re.compile(r'Takim.$')})
team_one, team_two = teams_tag[0].text, teams_tag[1].text

# Oyuncu Değişikliklerini al