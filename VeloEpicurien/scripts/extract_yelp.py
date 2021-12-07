import json
import os
import requests

BASE_URL = "https://api.yelp.com/v3/businesses/"

headers = {
  'Authorization': os.environ.get('YELP_AUTH')
}

restaurants_by_id = {}
limit = 50
offset = 0
while True:
    url = BASE_URL + f'search?location=Montreal&limit={limit}&offset={offset}'
    response = requests.request("GET", url, headers=headers, data={})
    response_json = json.loads(response.text)
    businesses = response_json['businesses']
    for business in businesses:
        restaurants_by_id[business['id']] = business
    offset += len(businesses)
    if len(businesses) == 0:
        break
restaurants = list(restaurants_by_id.values())
with open('restaurants.json', 'w') as out_file:
    json.dump(restaurants, out_file)
