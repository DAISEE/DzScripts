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
            abi = json.safe_load(data_file)
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


def switchEnergy(myEnergy, nodeChannel, sellerChannel):

    # the node consumes its "own" energy :
    # - nodeChannel is NC
    # - sellerChannel is NO
    if myEnergy:
        GPIO.output(Relay_channel[nodeChannel], GPIO.HIGH)
        GPIO.output(Relay_channel[sellerChannel], GPIO.HIGH)
    # the node consumes seller's energy :
    # - nodeChannel 0 is now open
    # - sellerChannel is now closed
    else:
        # node uses seller energy
        GPIO.output(Relay_channel[nodeChannel], GPIO.LOW)
        GPIO.output(Relay_channel[sellerChannel], GPIO.LOW)