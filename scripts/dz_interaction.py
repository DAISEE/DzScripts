from web3 import Web3, KeepAliveRPCProvider
import fct
import serial
import time

param = fct.loadparam()

def turnRelay(relai):
    global relai4_status

    if(relai == "4"):
        if relai4_status == 0:
            ser.write(str("4").encode())
            relai4_status = 1
        else:
            ser.write(str("4").encode())
            relai4_status = 0

# Connection to Ethereum
web3 = Web3(KeepAliveRPCProvider(host=param['contract']['node'], port='8545'))

# connection to the relay
ser = serial.Serial(param['relay']['serial'], 9600)

# initialisation # to update
relai4_status = 0
lampStatus = 0

#node parameters
node = param['usedNode']['id']
nodeAddress = param[node]['address']
nodeURL = param[node]['url']
nodeLogin = param[node]['login']
nodePswd = param[node]['password']
tokenContract = param['contract']['token']
sensorId = param[node]['sensorId']
headersTime = {'Content-Type': 'application/json', }
dataTime = 'login=' + nodeLogin + '&password=' + nodePswd

# Contract definition
daiseeAbi = fct.loadabi('daisee.sol.json')
daisee = web3.eth.contract(abi=daiseeAbi, address=param['contract']['address'])

# light bulb init
## getting energy balance
print('Get Energy Balance')
EnergyBalance = daisee.call({'from': param[node]['address']}).getEnergyBalance()
print(EnergyBalance)

if EnergyBalance >= param['node2']['limit'] :
    # the bulb is on
    turnRelay("4")
    lampStatus = int(ser.read())

time0 = fct.getDateTime(nodeURL, dataTime, headersTime)


while 1:
    # delay to define
    time.sleep(16)

    # getting energy produced or consumed
    time1 = fct.getDateTime(nodeURL, dataTime, headersTime)
    sumWatt = fct.getEnergySum(nodeURL, sensorId, dataTime, headersTime, time0, time1)

    print('time : ' + time.strftime("%D %H:%M:%S", time.localtime(int(time1))) + ', sumWatt = ' + str(sumWatt))

    time0 = time1

    if sumWatt !=0:

        # Consumer
        if param[node]['typ'] == 'C':

            # unlock account
            print('Unlock Account')
            unlockOK = web3.personal.unlockAccount(nodeAddress, param[node]['accountpswd'])
            print(' > unlockOK = ' + str(unlockOK))

            # updating Energy balance (consumer)
            print('ConsumeEnergy')
            result = daisee.transact({'from': nodeAddress}).consumeEnergy(sumWatt)
            print(' > result = ' + str(result))

            # getting the energy balance
            print('Get Energy Balance')
            EnergyBalance = daisee.call({'from': param[node]['address']}).getEnergyBalance()
            print(' > EnergyBalance = ' + str(EnergyBalance))

            # if energy balance is too low, a energy transaction is triggered
            if EnergyBalance < param[node]['limit']:
                print(lampStatus)
                if lampStatus == 1:
                    print('yes')
                    turnRelay("4")
                    lampStatus = int(ser.read())

                # unlock account
                print('Unlock Account')
                unlockOK = web3.personal.unlockAccount(nodeAddress, param[node]['accountpswd'])
                print(' > unlockOK = ' + str(unlockOK))

                print('Buy Energy')
                # attention à l'allowance
                watt = 200 # to adjust
                # for DEBUG/TESTING, node2 is selected by default
                seller = param['node2']['address'].replace('0x', '')
                ret = daisee.transact({'from': nodeAddress}).buyEnergy(tokenContract, seller, watt)
                print(' > result = ' + str(result))

                time.sleep(2)

                turnRelay("4")
                lampStatus = int(ser.read())
                print(lampStatus)

        # Producer
        else:
            # unlock account
            print('Unlock Account')
            unlockOK = web3.personal.unlockAccount(nodeAddress, param[node]['accountpswd'])
            print(' > unlockOK = ' + str(unlockOK))

            # to update Energy balance (producer)
            print('SetProduction')
            result = daisee.transact({'from': nodeAddress}).setProduction(sumWatt)
            print(' > result = ' + str(result))