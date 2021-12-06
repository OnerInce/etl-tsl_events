from pymongo import MongoClient

client = MongoClient(
    "mongodb://oner_admin:bk6hWgp8LKHQfy16@tsl-events-db-shard-00-00.oar7f.mongodb.net:27017,tsl-events-db-shard-00-01.oar7f.mongodb.net:27017,tsl-events-db-shard-00-02.oar7f.mongodb.net:27017/myFirstDatabase?ssl=true&replicaSet=atlas-3xhrl0-shard-0&authSource=admin&retryWrites=true&w=majority")
db = client.tsl_events

mycol = db["events_collection"]

random_doc = mycol.aggregate([
    {'$sample': {'size': 1}}
])

print((list(random_doc))[0]['_id'])

# mycol.delete_one({'_id': ObjectId(_id)})
