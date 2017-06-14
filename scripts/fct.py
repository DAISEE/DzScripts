import json
import requests
import sys
import yaml


def loadparam():
    with open("parameters.yml", 'r') as stream:
        try:
            param = yaml.safe_load(stream)
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
        try:
            result = requests.post(url + '/api/time', headers=headersTime, data=dataTime)
        except Exception as e:
            print(e)
        else:
            parsed_json = json.loads(result.text)
            return parsed_json['data']
    except json.JSONDecodeError as e:
        print("ERROR -  getDateTime( : " + str(e))
        return ""


def getEnergySum(url, sensorId, dataTime, headersTime, t0, t1):
    print("fct.GetEnergySum")
    sumEnergy = 0
    timestp = 0

    try:
        result = requests.post(url + '/api/' + str(sensorId) + '/get/watts/by_time/' + str(t0) + '/' + str(t1), headers=headersTime, data=dataTime)
    except json.JSONDecodeError as e:
        print(e)
    else:
        parsed_json = json.loads(result.text)
        for n in range(0, len(parsed_json['data'])):
            # TODO : check data from citizenwatt
            if timestp < parsed_json['data'][n]['timestamp']:
                watt = int(parsed_json['data'][n]['value'])
                print(' > watt = ' + str(watt))
                sumEnergy += watt
                timestp = parsed_json['data'][n]['timestamp']

    if sumEnergy < 0:
        sumEnergy = 0

    return sumEnergy

def getSoC(filename):
    print("fct.getSoC")
    FileTemp = open(filename, 'r')

    for i in range(1):
        for attempt in range(3):
            try:
                measure = FileTemp.read()
                measure = measure.split(',')
                data = measure[0].split('|')
                soc = float(data[0])
            except Exception as e:
                print("ERROR : Incorrect data from sensor log - attempt: " + str(attempt + 1) + " : " + str(e))
                continue
            break
        else:
            print("ERROR : Incorrect data from sensor log > all attempts failed. \r\nExiting")
            sys.exit(1)
    return soc