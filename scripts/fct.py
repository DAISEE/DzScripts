import json
import requests
import sys
import yaml


def loadparam():
    with open("parameters.yml", 'r') as stream:
        try:
            param = yaml.load(stream)
        except yaml.YAMLError as e:
            print(e)
            sys.exit(1)
        else:
            return param


def loadabi(jsonfile):
    with open(jsonfile) as data_file:
        try:
            abi = json.load(data_file)
        except json.JSONDecodeError as e:
            print(e)
            sys.exit(1)
        else:
            return abi


def getDateTime(url, dataTime, headersTime):
    try:
        result = requests.post(url + '/api/time', headers=headersTime, data=dataTime)
        parsed_json = json.loads(result.text)
        return parsed_json['data']
    except json.JSONDecodeError as e:
        print(e)


def getEnergySum(url, sensorId, dataTime, headersTime, t0, t1):
    sumEnergy = 0
    timestp = 0

    try:
        result = requests.post(url + '/api/' + str(sensorId) + '/get/watts/by_time/' + str(t0) + '/' + str(t1), headers=headersTime, data=dataTime)
    except json.JSONDecodeError as e:
        print(e)
    else:
        print('result : ' + str(result))
        parsed_json = json.loads(result.text)
        print('parsed_json : ' + str(parsed_json))
        for n in range(0, len(parsed_json['data'])):
            print("parsed_json['data'][n]['timestamp'] : " + str(parsed_json['data'][n]['timestamp']))
            # TODO : check data from citizenwatt
            if timestp < parsed_json['data'][n]['timestamp']:
                watt = int(parsed_json['data'][n]['value']) # /100 for test and debug
                print('watt + ' + str(watt))
                sumEnergy += watt
                timestp = parsed_json['data'][n]['timestamp']
    return sumEnergy

def turnRelay(relai):
    global relai4_status

    if(relai == "4"):
        if relai4_status == 0:
            ser.write(str("4").encode())
            relai4_status = 1
        else:
            ser.write(str("4").encode())
            relai4_status = 0