import json

with open('db/costume_2.json','r') as fp:
    costumes = json.load(fp)

JOB_IDS = 4350
for costume in costumes:
    print(costume + " = " + str(JOB_IDS) + ",")
    JOB_IDS += 1

for costume,sprite in costumes.items():
    print("[PCIds." + costume + "] = \"" + sprite + "\",")

for costume,sprite in costumes.items():
    print("[PCIds." + costume + "] = \"" + "body" + "\",")


for costume,sprite in costumes.items():
    print("[PCIds." + costume + "] = \"" + sprite + "\\\\"+sprite+"\",")

for costume,sprite in costumes.items():
    print("[PCIds." + costume + "] = \"" + costume.lower().replace("_"," ").capitalize()[:-1] + "\",")