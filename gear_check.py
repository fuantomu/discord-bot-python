import requests
import xmltodict
import ast
import re
import json

slots = {
    0 : "Helmet",
    1 : "Neck",
    2 : "Shoulder",
    4 : "Chest",
    5 : "Belt",
    6 : "Pants",
    7 : "Boots",
    8 : "Bracers",
    9 : "Gloves",
    10 : "Finger 1",
    11 : "Finger 2",
    12 : "Trinket 1",
    13 : "Trinket 2",
    14 : "Cloak",
    15 : "Mainhand",
    16 : "Offhand",
    17 : "Ranged/Relic",
}

ignore_slots = [3,12,13,18]

ignore_enchant = [1,5,12,13,17]

wowhead_link = 'https://www.wowhead.com/cata/item=ITEMID?xml'

zone_min_itemlevel = {
    1023: 346
}

gem_class = {
    0: [0], # Red
    1: [1], # Blue
    2: [2], # Yellow
    3: [0,1], # Purple
    4: [1,2], # Green
    5: [0,2] # Orange
}

roles = {
    "tank": ["Blood","Guardian","Protection"],
    "caster": ["Fire","Arcane","Frost","Affliction","Demonology","Destruction","Elemental","Shadow","Balance","Restoration","Holy","Discipline"],
    "dps": ["Enhancement","Feral","Fury","Arms","Assassination","Combat","Subtlety","Unholy","Frost","Retribution","Fire","Arcane","Frost","Affliction","Demonology","Destruction","Elemental","Shadow","Balance","Beastmastery","Survival","Marksmanship"],
    "melee": ["Enhancement","Feral","Fury","Arms","Assassination","Combat","Subtlety","Unholy","Frost","Retribution"],
    "ranged": ["Beastmastery","Survival","Marksmanship"],
    "healer": ["Restoration","Holy","Discipline"]
}

class_types = {
    "strength": ["Unholy","Frost","Retribution","Fury","Arms"],
    "agility": ["Enhancement","Feral","Beastmastery","Survival","Marksmanship","Assassination","Combat","Subtlety"]
}



item_cache = {}
with open("cataclysm/items.json", "r") as f:
    item_cache = json.load(f)
    print(f"Loaded {len(item_cache)} items from cache")

enchants = {}
def load_enchants():
    try:
        global enchants
        enchants = requests.get('https://raw.githubusercontent.com/fuantomu/envy-armory/main/enchants.json').json()
        print(f"Loaded {sum([len(enchants[slot]) for slot in enchants])} enchants")
    except:
        print("ERROR: Could not load enchants")
load_enchants()

def check_gear(gear, zone, spec):
    output = {
        "minor": "",
        "major": "",
        "extreme": ""
    }
    sockets = {0:0,1:0,2:0}
    professions = {"enchanting": {"found": 0, "items": []}, "blacksmithing": {"found": 0, "items": []}, "jewelcrafting": {"found": 0, "items": []}, "tailoring": {"found": 0, "items": []}, "engineering": {"found": 2, "items": []}, "inscription": {"found": 0, "items": []}, "leatherworking": {"found": 0, "items": []}, "alchemy": {"found": 0, "items": []}}
    meta = None
    for item in gear:
        if item["slot"] in ignore_slots or item["id"] == 0:
            continue

        item_stats = get_wowhead_item(item["id"])
        
        if item["itemLevel"] < zone_min_itemlevel[zone]:
            output["extreme"] += f"{item.get('name', '')} ({slots[item['slot']]}) itemlevel is <346\n"
        
        if item["slot"] not in ignore_enchant:
            if item.get("permanentEnchant") is None: 
                if not item["slot"] in [10,11]: # if ring
                    output["extreme"] += f"{item.get('name', '')} ({slots[item['slot']]}) missing enchant\n"
                else:
                    professions["enchanting"]["items"].append(item)
            else:
                found_enchant = False
                for enchant in enchants[str(item["slot"])]:
                    if enchant["id"] == item["permanentEnchant"]:
                        
                        found_enchant = True
                        if enchant["tier"] >= 2:
                            output["major"] += f"{item.get('name', '')} ({slots[item['slot']]}) has a very low level enchant: {enchant['name']}\n"
                        if enchant["tier"] == 1:
                            output["minor"] += f"{item.get('name', '')} ({slots[item['slot']]}) has a low level enchant: {enchant['name']}\n"
                        
                        unsuited_enchant_found = False
                        if enchant.get("role") is not None:
                            if spec not in roles[enchant["role"]] and spec != enchant.get("spec"):
                                unsuited_enchant_found = True
                                output["minor"] += f"{item.get('name', '')} ({slots[item['slot']]}) has an enchant that is not suited for their role ({spec}): {enchant['name']} ({enchant['role']})\n"
                        if enchant.get("type") is not None and not unsuited_enchant_found:
                            if spec not in class_types[enchant["type"]] and spec != enchant.get("spec"):
                                output["minor"] += f"{item.get('name', '')} ({slots[item['slot']]}) has an enchant that is not suited for their type ({spec}): {enchant['name']} ({enchant['type']})\n"
                        
                        if item["slot"] in [10,11]:
                            professions["enchanting"]["found"] += 1
                            
                        if item["slot"] == 6:
                            if enchant["id"] in [4439,4440]:
                                professions["leatherworking"]["found"] += 1
                            else:
                                professions["leatherworking"]["items"].append(item)
                            if enchant["id"] in [4113,4114]:
                                professions["tailoring"]["found"] += 1
                            else:
                                professions["tailoring"]["items"].append(item)
                        if item["slot"] == 8:
                            if enchant["id"] in [4189,4191,4192]:
                                professions["leatherworking"]["found"] += 1
                            else:
                                professions["leatherworking"]["items"].append(item)
                        if item["slot"] == 2:
                            if enchant["id"] in [4193,4194,4195,4196]:
                                professions["inscription"]["found"] += 1
                            else:
                                professions["inscription"]["items"].append(item)
                        if item["slot"] == 14:
                            if enchant["id"] in [4115,4116,4118]:
                                professions["tailoring"]["found"] += 1
                            else:
                                professions["tailoring"]["items"].append(item)
                            
                if not found_enchant:
                    output["extreme"] += f"{item.get('name', '')} ({slots[item['slot']]}) has an incorrect enchant (Unknown enchant or low level)\n"
                    with open(f"unknown_enchants","a") as f:
                        f.write(f"\n{slots[item['slot']]}\n")
                        f.write(f'{str(item["permanentEnchant"])} - {str(item.get("permanentEnchantName", "Unknown name"))}')
                
            
        if item["slot"] == 5 and item.get("onUseEnchant") != 4223: # Nitro Boots
            output["major"] += f"{item.get('name', '')} ({slots[item['slot']]}) missing Nitro Boots\n"
            professions["engineering"]["found"] -= 1
            professions["engineering"]["items"].append(item)
        if item["slot"] == 9 and item.get("onUseEnchant") != 4179 and spec not in ["Guardian","Blood","Protection"] : # Synapse Springs
            output["major"] += f"{item.get('name', '')} ({slots[item['slot']]}) missing Synapse Springs\n"
            professions["engineering"]["found"] -= 1
            professions["engineering"]["items"].append(item)
        elif item["slot"] == 9 and item.get("onUseEnchant") != 4180 and spec in ["Guardian","Blood","Protection"] : # Quickflip Deflection Plates
            output["major"] += f"{item.get('name', '')} ({slots[item['slot']]}) missing Quickflip Deflection Plates\n"
            professions["engineering"]["found"] -= 1
            professions["engineering"]["items"].append(item)

        if item["slot"] == 5 and len(item.get("gems", [])) < item_stats.get("nsockets", 0)+1:
            output["extreme"] += f"{item.get('name', '')} ({slots[item['slot']]}) missing a belt buckle\n"
        
        if item.get("gems") is not None:
            if any([gem["itemLevel"] < 85 for gem in item["gems"]]):
                output["major"] += f"{item.get('name', '')} ({slots[item['slot']]}) has a low level gem\n"
            for gem in item["gems"]:
                if "meta" in gem["icon"]:
                    meta = get_wowhead_item(gem["id"])
                    continue
                
                if "dragonseye" in gem["icon"]:
                    professions["jewelcrafting"]["found"] += 1
                    professions["jewelcrafting"]["items"].append(item)
                gem_stats = get_wowhead_item(gem["id"])
                if gem_stats["color"] != 10 :
                    for color in gem_class[gem_stats["color"]]:
                        sockets[color] += 1

        if len(item.get("gems", [])) < item_stats.get("nsockets", 0):
            output["extreme"] += f"{item.get('name', '')} ({slots[item['slot']]}) has {item_stats['nsockets']-len(item.get('gems', []))} empty socket(s)\n"
        
        if item["slot"] in [8,9]:
            if len(item.get("gems", [])) > item_stats.get("nsockets", 0):
                professions["blacksmithing"]["found"] +=1
            else:
                professions["blacksmithing"]["items"].append(item)
                
        if item["slot"] in [12,13]:
            print(item["id"])
            if item["id"] in [58483,68775,68776,68777]:
                professions["alchemy"]["found"] +=1

    total_professions = [profession[0].capitalize() for profession in professions.items() if profession[1]["found"] > 0]
    for profession in professions.items():
        if profession[1]['found'] > 0:
            if profession[0] == "enchanting" and profession[1]['found'] != 2:
                output["extreme"] += f"{profession[1]['items'][0].get('name', '')} ({slots[profession[1]['items'][0]['slot']]}) missing enchanting-specific enchant\n"
            if profession[0] == "blacksmithing" and profession[1]['found'] != 2:
                output["extreme"] += f"{profession[1]['items'][0].get('name', '')} ({slots[profession[1]['items'][0]['slot']]}) missing blacksmithing socket\n"
            if profession[0] == "jewelcrafting" and profession[1]['found'] != 3:
                item_text = ','.join([f"{found_item.get('name', '')} ({slots[profession[1]['items'][0]['slot']]})" for found_item in profession[1]['items']])
                output["extreme"] += f"{item_text} missing {3-profession[1]['found']} jewelcrafting gems\n"
            if profession[0] == "engineering" and profession[1]['found'] != 2:
                item_text = ','.join([f"{found_item.get('name', '')} ({slots[profession[1]['items'][0]['slot']]})" for found_item in profession[1]['items']])
                output["extreme"] += f"{item_text} missing engineering enchants\n"
            if profession[0] == "leatherworking" and profession[1]['found'] != 2:
                output["extreme"] += f"{profession[1]['items'][0].get('name', '')} ({slots[profession[1]['items'][0]['slot']]}) missing leatherworking enchant\n"
            if profession[0] == "tailoring" and profession[1]['found'] != 2:
                output["extreme"] += f"{profession[1]['items'][0].get('name', '')} ({slots[profession[1]['items'][0]['slot']]}) missing tailoring enchant\n"
    
    if len(total_professions) < 2:
        output["extreme"] += f"Only one primary profession bonus found: {','.join(total_professions)}\n"

    if meta is None:
        output["extreme"] += f"No meta gem\n"
    else:
        if any([sockets[int(k)] < v for k,v in meta["meta"].items()]):
            output["extreme"] += f"Meta gem is not active!\n"
            
    with open("cataclysm/items.json", "w") as f:
        json.dump(item_cache, f)

    return output

def get_wowhead_item(id):
    if item_cache.get(str(id)) is None:
        print(f"Requesting item {id} from wowhead")
        wowhead_response = requests.get(wowhead_link.replace("ITEMID", str(id)))
        parsed_xml = xmltodict.parse(wowhead_response.content)
        
        parsed_item = ast.literal_eval("{ " + parsed_xml["wowhead"]["item"]["jsonEquip"] + " }")
        if parsed_xml["wowhead"]["item"]["class"]['#text'] == "Gems":
            # if item is gem, parse html data for meta requirements
            if parsed_xml["wowhead"]["item"]["subclass"]['#text'] == "Meta Gems":
                parsed_item["meta"] = {}

                requirements = re.findall(r'<div class="q0">(.*?)<\/div>', parsed_xml["wowhead"]["item"]["htmlTooltip"])[0].split("<br />")
                for entry in requirements:
                    if "Red" in entry:
                        parsed_item["meta"][0] = int(re.findall(r'([0-9])', entry)[0])
                    elif "Blue" in entry:
                        parsed_item["meta"][1] = int(re.findall(r'([0-9])', entry)[0])
                    elif "Yellow" in entry:
                        parsed_item["meta"][2] = int(re.findall(r'([0-9])', entry)[0])
            else:
                parsed_item["color"] = int(parsed_xml["wowhead"]["item"]["subclass"]['@id'])
        item_cache[str(id)] = parsed_item
    return item_cache[str(id)]