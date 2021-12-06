import os
import ssl
import time

import requests
import urllib3
from bs4 import BeautifulSoup
from smart_open import open

MAIN_PAGE = "https://tff.org/default.aspx?pageID=545"
FIRST_VALID_SEASON_URL = "https://www.tff.org/default.aspx?pageID=1529"

ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_valid_season_urls():
    """
    get urls of the season pages, starting from FIRST_VALID_SEASON_URL
    """

    print("Getting season urls...")

    content = requests.get(MAIN_PAGE, verify=ssl.CERT_NONE).content
    soup = BeautifulSoup(content, "html.parser")

    seasons_td = soup.find_all("td", attrs={"class": "alanSuperLig"})
    seasons_td = [x for x in seasons_td if "Şampiyonlukları" in x.text][0]

    table_element = seasons_td.findParents('table')[0]

    seasons = table_element.findChildren("a")
    seasons = [x["href"] for x in seasons]
    last_valid_season_index = seasons.index(FIRST_VALID_SEASON_URL)

    valid_seasons = []
    for e, season in enumerate(seasons):
        if e < last_valid_season_index:
            continue
        valid_seasons.append(season)
    print(valid_seasons)
    return valid_seasons


def get_all_weeks_urls(season_url):
    """
    get urls of all weeks of the season :season_url
    """

    print("Getting week urls...")

    content = requests.get(season_url, verify=ssl.CERT_NONE).content
    soup = BeautifulSoup(content, "html.parser")
    all_weeks = soup.find_all("td", attrs={"class": ["haftaNoOn", "haftaNoOff", "haftaNoActive"]})
    all_weeks = ["http://www.tff.org/" + x.findChild("a")['href'] for x in all_weeks]

    return all_weeks[:int(len(all_weeks) / 2)]


def get_single_weeks_matches(week_url):
    """
    get all match urls of the week :week_url
    """

    print("Getting match urls...")

    content = requests.get(week_url, verify=ssl.CERT_NONE, headers={"User-agent":
                                                                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"}).content
    soup = BeautifulSoup(content, "html.parser")

    weeks_matches_anchor = soup.findAll('a', id=lambda x: x and "HaftaninMaclari" in x)
    weeks_matches_urls = ["http://www.tff.org/" + x["href"] for x in weeks_matches_anchor if "kulup" not in x["href"]]

    weeks_matches_urls = list(set(weeks_matches_urls))

    return weeks_matches_urls


def save_match_urls_to_s3():
    """
    save .txt file of all match urls to s3
    """

    print("Match urls fetching...")

    all_match_urls = []

    all_seasons = get_valid_season_urls()
    for season in all_seasons:
        week_urls = get_all_weeks_urls(season)
        for e, week in enumerate(week_urls):
            print('Week', e + 1)
            match_urls = get_single_weeks_matches(week)
            all_match_urls.extend(match_urls)
            time.sleep(1)  # avoid rate limit

    print('Saving match urls to s3...')

    with open(f"s3://{os.environ['BUCKET_NAME']}/match_urls.txt", 'w') as f:
        for item in all_match_urls:
            f.write("%s\n" % item)
