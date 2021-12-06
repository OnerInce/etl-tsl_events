from extract.save_match_urls_s3 import save_match_urls_to_s3
from load.insert_to_mongo import save_event_mongo
from transform.parse_match_data import create_match_obj_list

# parse all match urls for all seasons and save to s3 (extract)
save_match_urls_to_s3()

# create Match objects from parsed html to store match information  (transform)
match_objects = create_match_obj_list()

# save match events to mongo (load)
save_event_mongo(match_objects)
