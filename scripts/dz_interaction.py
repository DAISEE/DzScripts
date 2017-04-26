import json
import requests
import serial
import time
import yaml


def padhexa(s):
    return s[2:].zfill(64)


def padaddress(a):
    a = a.strip('0x')
    a = a.rjust(64, '0')
    return a


def ethrequest(method, params):
    headers = {'Content-Type': 'application/json',}
    data = '{"jsonrpc":"2.0",' \
           '"method":' + method + ',' \
           '"params":[' + params + '],' \
           '"id":1}'
    result = requests.post(host, headers=headers, data=data)
    try:
        parsed_json = json.loads(result.text)
    except:
        parsed_json = ''
    else:
        print(' > result.text = ' + str(result.text))

    return parsed_json


def getDateTime(url, dataTime, headersTime):
    try:
        result = requests.post(url + '/api/time', headers=headersTime, data=dataTime)
        parsed_json = json.loads(result.text)
        return parsed_json['data']
    except json.JSONDecodeError as e:
        print(e)


def getEnergySum(url, dataTime, headersTime, t0, t1):
    sumEnergy = 0
    timestp = 0
    sensorId = param[node]['sensorId']

    try:
        result = requests.post(url + '/api/' + str(sensorId) + '/get/watts/by_time/' + str(t0) + '/' + str(t1), headers=headersTime, data=dataTime)
    except json.JSONDecodeError as e:
        print(e)
    else:
        parsed_json = json.loads(result.text)
        for n in range(0, len(parsed_json['data'])):
            print("parsed_json['data'][n]['timestamp'] : " + str(parsed_json['data'][n]['timestamp']))
            # TODO : check data from citizenwatt
            if timestp < parsed_json['data'][n]['timestamp']:
                watt = int(parsed_json['data'][n]['value'])
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


with open("parameters.yml", 'r') as stream:
    try:
        param = yaml.load(stream)
    except yaml.YAMLError as e:
        print(e)


# Connection to Ethereum
host = 'http://' + param['contract']['node'] + ':8545'

# connection to the relay
ser = serial.Serial(param['relay']['serial'], 9600)

# initialisation # to update
relai4_status = 0
lampStatus = 0

# Defintion of node used to update data
node = param['usedNode']['id']
nodeURL = param[node]['url']
nodeLogin = param[node]['login']
nodePswd = param[node]['password']
tokenContract = param['contract']['token']
headersTime = {'Content-Type': 'application/json', }
dataTime = 'login=' + nodeLogin + '&password=' + nodePswd

# light bulb init
## getting energy balance
data = '{"from":"' + param[node]['address'] + '","to":"' + param['contract']['address'] + '","data":"' + param['contract']['fctEnergyBalance'] + '"}, "latest"'
result = ethrequest('"eth_call"', data)
EnergyBalance = int(result['result'], 0)

if EnergyBalance >= param['node2']['limit'] :
    # the bulb is on
    turnRelay("4")
    lampStatus = int(ser.read())

time0 = getDateTime(nodeURL, dataTime, headersTime)


while 1:
    # delay to define
    time.sleep(16)

    # getting energy produced or consumed
    time1 = getDateTime(nodeURL, dataTime, headersTime)
    sumWatt = getEnergySum(nodeURL, dataTime, headersTime, time0, time1)

    print('time : ' + time.strftime("%D %H:%M:%S", time.localtime(int(time1))) + ', sumWatt = ' + str(sumWatt))

    time0 = time1

    if sumWatt !=0 :

        # Consumer
        if param[node]['typ'] == 'C':

            # unlock account
            print('Unlock Account')
            data = '"' + param[node]['address'] + '","' + param[node]['accountpswd'] + '",null'
            result = ethrequest('"personal_unlockAccount"', data)
            print(' > result = ' + str(result))

            # updating Energy balance (consumer)
            print('ConsumeEnergy')
            hashData = param['contract']['fctConsumeEnergy'] + padhexa(hex(sumWatt))
            data = '{"from":"' + param[node]['address'] + '","to":"' + param['contract']['address'] + '","data":"' + hashData + '"}'
            result = ethrequest('"eth_sendTransaction"', data)
            print(' > result = ' + str(result))

            # getting the energy balance
            print('Get Energy Balance')
            data = '{"from":"' + param[node]['address'] + '","to":"' + param['contract']['address'] + '","data":"' + \
                   param['contract']['fctEnergyBalance'] + '"}, "latest"'
            result = ethrequest('"eth_call"', data)
            print(' > result = ' + str(result))
            EnergyBalance = int(result['result'], 0)

            # if energy balance is too low, a energy transaction is triggered
            if EnergyBalance < param[node]['limit']:
                print(lampStatus)
                if lampStatus == 1:
                    print('yes')
                    turnRelay("4")
                    lampStatus = int(ser.read())

                # unlock account
                print('Unlock Account')
                data = '"' + param[node]['address'] + '","' + param[node]['accountpswd'] + '",null'
                result = ethrequest('"personal_unlockAccount"', data)
                print(' > result = ' + str(result))

                print('Buy Energy')
                # beware of tokens allowed
                watt = 200 # to adjust
                # for DEBUG/TESTING, node2 is selected by default
                seller = param['node2']['address'].replace('0x', '')
                hashData = param['contract']['fctBuyEnergy'] + padaddress(tokenContract) + padaddress(seller) + padhexa(hex(watt))
                data = '{"from":"' + param[node]['address'] + '","to":"' + param['contract']['address'] + '","data":"' + hashData + '"}'
                result = ethrequest('"eth_sendTransaction"', data)
                print(' > result = ' + str(result))

                #time.sleep(2)

                turnRelay("4")
                lampStatus = int(ser.read())
                print(lampStatus)

        # Producer
        else:
            # unlock account
            print('Unlock Account')
            data = '"' + param[node]['address'] + '","' + param[node]['accountpswd'] + '",null'
            result = ethrequest('"personal_unlockAccount"', data)

            # to update Energy balance (producer)
            print('SetProduction')
            hashData = param['contract']['fctSetProduction'] + padhexa(hex(sumWatt))
            data = '{"from":"' + param[node]['address'] + '","to":"' + param['contract']['address'] + '","data":"' + hashData + '"}'
            result = ethrequest('"eth_sendTransaction"', data)
            print(' > result = ' + str(result))
