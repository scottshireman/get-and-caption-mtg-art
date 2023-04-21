import json
import requests
import time
import shutil
import re
import os
from unidecode import unidecode

## You need to go to https://scryfall.com/docs/api/bulk-data and download
## the Unique Artwork JSON file. Put the relative path to the file here:
PATH_TO_SCRYFALL_JSON = 'unique-artwork-20230418210416.json'

def download_image(art_url, file_name):

    if not os.path.exists(f"images/{file_name}.jpg"):
        time.sleep(0.5)
        r = requests.get(art_url)
        time.sleep(0.5)
        r = requests.get(r.url, stream=True)
        if r.status_code == 200:            #200 status code = OK
            with open(f"images/{file_name}.jpg", 'wb') as f: 
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
                
        f.close()
    else:
        print(f"Already downloaded images/{file_name}.jpg")

def write_card_tags(i, file_name, card_rarity, set_name, card_layout, uri):
    tags = []

    arrays = ['promo_types', 'keywords']
    special = ['cmc','flavor_text']

    print (i['name'], file_name, card_layout, uri)

    tags.append(f"named {i['name'].replace(',','')}")
    tags.append(card_rarity)

    if card_layout == 'token':
        tags.append(card_layout)

    colors = i['colors']
    for entry in colors:
        tags.append(f"{mtg_colors[entry]}")


    for index in arrays:
        try:
            for entry in i[index]:
                tags.append(f"{entry.lower()}")
        except KeyError:
            time.sleep(0.1)

    types = i['type_line'].split(" ") #(" — ")
    for entry in types:
        if entry != "—":
            tags.append(f"{entry.lower()}")

    oracle_text = unidecode(i['oracle_text'])
    oracle_text = re.sub("[\(\[].*?[\)\]]", "", oracle_text)
    # print(oracle_text)
    oracle_tags = []
    
    for stop_word in stop_words:
        oracle_text = oracle_text.replace(stop_word, '_')

    for oracle_phrase in oracle_text.split("_"):
        oracle_phrase = oracle_phrase.strip().lower()
        if oracle_phrase != '' and oracle_phrase != 'otherwise' and oracle_phrase not in tags:
            tags.append(f"{oracle_phrase}")

    tags.append(f"from {set_name}")
    tags.append(f"by {unidecode(i['artist'])}")

    with open(f"images/{file_name}.txt", 'w') as f: 
        f.write(", ".join(tags))

    f.close()

mtg_colors = {
            "W": "white",
            "U": "blue",
            "B": "black",
            "R": "red",
            "G": "green"
            }

stop_words = [',', '.','\n']

multiface_card_types = ['transform', 'double_faced_token', 'modal_dfc']
skip_types = ['flip', 'reversible_card', 'art_series', 'split', 'adventure'] 
  
# Opening JSON file
f = open(PATH_TO_SCRYFALL_JSON, encoding='utf8')

# returns JSON object as 
# a dictionary
data = json.load(f)

#print(data[0])

start_time = time.time()

for i in data:

    if i['layout'] in multiface_card_types:
        print(f"{i['name']}\t{i['id']} is multiface")

        #Front
        face_name = f"{i['id']}_front"
        art_url = "https://api.scryfall.com/cards/" + i['id'] + "?format=image&version=art_crop&face=front"
        write_card_tags(i['card_faces'][0], f"{face_name}", i['rarity'], i['set_name'], i['layout'], i['scryfall_uri'])
        download_image(art_url, f"{face_name}")

        #Back
        face_name = f"{i['id']}_back"
        art_url = "https://api.scryfall.com/cards/" + i['id'] + "?format=image&version=art_crop&face=back"
        write_card_tags(i['card_faces'][1], f"{face_name}", i['rarity'], i['set_name'], i['layout'], i['scryfall_uri'])
        download_image(art_url, f"{face_name}")

            
    elif i['layout'] not in skip_types:
        card_name = f"{i['id']}"
        art_url = "https://api.scryfall.com/cards/" + i['id'] + "?format=image&version=art_crop"

        write_card_tags(i, f"{card_name}", i['rarity'], i['set_name'], i['layout'], i['scryfall_uri'])
        download_image(art_url, f"{card_name}")

