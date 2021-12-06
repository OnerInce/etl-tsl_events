import os
from pprint import pprint

from pymongo import MongoClient

mongo_uri = f'mongodb://{os.environ["MONGO_INITDB_ROOT_USERNAME"]}:{os.environ["MONGO_INITDB_ROOT_PASSWORD"]}@{os.environ["MONGO_HOST"]}:27017/'

client = MongoClient(mongo_uri)
db = client[os.environ["MONGO_INITDB_DATABASE"]]
collection = db[os.environ["MONGO_COLLECTION"]]


def save_event_mongo(match_list):
    """
    save all events of each match as json to mongo
    """
    for m in match_list:
        events = m.events_array
        if len(events) == 0:
            continue

        pprint(f'{events[0]["match_start_date"]} - {events[0]["home_team"]} - {events[0]["away_team"]}')

        for event in events:
            result = collection.insert_one(event)
            print('Created as {0}'.format(result.inserted_id))
