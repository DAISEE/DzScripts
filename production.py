#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Project : Daisee
Date : 2017-02-16, by caroline kogel
Description :
        Push Data to ethereum node
        Example:
               daisee -f file.csv
"""

# IMPORTS
import csv
import argparse
import json
import time
from collections import defaultdict
from web3 import Web3, KeepAliveRPCProvider, IPCProvider

# GET PARAMETERS
parser = argparse.ArgumentParser(description='Push data to ethereum node')
parser = argparse.ArgumentParser(add_help=True)

parser.add_argument('-f', action="store", dest="file", type=str, required=True, help="CSV file")

options = parser.parse_args()
FILE = options.file

# GLOBALE PAREMTERES
DATA = 0
WEB3 = Web3(KeepAliveRPCProvider(host='localhost', port='8545'))
COINBASE = WEB3.eth.coinbase
MINE_STATUS = WEB3.eth.mining
ADDRESS = '0xcf961c1b5becf104eb57cdafe360df4bd3731302'
ABI = json.loads('[{"constant":false,"inputs":[],"name":"getEnergyConsumption","outputs":[{"name":"energyBal","type":"uint256"}],"payable":false,"type":"function"},{"constant":false,"inputs":[],"name":"getReturn","outputs":[{"name":"","type":"uint256"}],"payable":false,"type":"function"},{"constant":true,"inputs":[],"name":"ret","outputs":[{"name":"","type":"uint256"}],"payable":false,"type":"function"},{"constant":false,"inputs":[{"name":"energy","type":"uint256"}],"name":"consumeEnergy","outputs":[{"name":"EnergyBal","type":"uint256"}],"payable":false,"type":"function"},{"constant":false,"inputs":[{"name":"seller","type":"address"},{"name":"energy","type":"uint256"}],"name":"buyEnergy","outputs":[{"name":"transactionOK","type":"bool"}],"payable":true,"type":"function"},{"constant":false,"inputs":[{"name":"adrs","type":"address"}],"name":"sendEther","outputs":[{"name":"","type":"bool"}],"payable":true,"type":"function"},{"constant":false,"inputs":[{"name":"kwh","type":"uint256"}],"name":"setProduction","outputs":[{"name":"EnergyBal","type":"uint256"}],"payable":false,"type":"function"},{"constant":false,"inputs":[],"name":"getRate","outputs":[{"name":"energyRate","type":"uint256"}],"payable":false,"type":"function"},{"constant":false,"inputs":[],"name":"getSold","outputs":[{"name":"energySold","type":"uint256"}],"payable":false,"type":"function"},{"constant":false,"inputs":[],"name":"getEnergyBalance","outputs":[{"name":"energyBal","type":"uint256"}],"payable":false,"type":"function"},{"constant":false,"inputs":[],"name":"getGain","outputs":[{"name":"finneyGain","type":"uint256"}],"payable":false,"type":"function"},{"constant":false,"inputs":[],"name":"receiveEther","outputs":[{"name":"","type":"bool"}],"payable":true,"type":"function"},{"constant":false,"inputs":[{"name":"adrs","type":"address"}],"name":"getSent","outputs":[{"name":"","type":"uint256"}],"payable":false,"type":"function"},{"inputs":[],"payable":true,"type":"constructor"},{"anonymous":false,"inputs":[{"indexed":false,"name":"from","type":"address"},{"indexed":false,"name":"kwh","type":"uint256"}],"name":"Prod","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"name":"from","type":"address"},{"indexed":false,"name":"energy","type":"uint256"}],"name":"Cons","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"name":"from","type":"address"},{"indexed":false,"name":"to","type":"address"},{"indexed":false,"name":"energy","type":"uint256"}],"name":"Buy","type":"event"}]')
CONTRACT = WEB3.eth.contract(abi = ABI, address = ADDRESS)
BYTECODE = "6060604052341561000c57fe5b5b66354a6ba7a180006000819055505b5b6106e68061002c6000396000f30060606040523615610081576000357c0100000000000000000000000000000000000000000000000000000000900463ffffffff16806313a59e3814610083578063298d65a1146100a957806336fd7e1b146100dd578063567cc2b614610134578063679aefce146101685780638da5cb5b1461018e57806399e1d301146101e0575bfe5b341561008b57fe5b610093610206565b6040518082815260200191505060405180910390f35b34156100b157fe5b6100c7600480803590602001909190505061024e565b6040518082815260200191505060405180910390f35b34156100e557fe5b61011a600480803573ffffffffffffffffffffffffffffffffffffffff169060200190919080359060200190919050506103a7565b604051808215151515815260200191505060405180910390f35b341561013c57fe5b610152600480803590602001909190505061055d565b6040518082815260200191505060405180910390f35b341561017057fe5b610178610641565b6040518082815260200191505060405180910390f35b341561019657fe5b61019e61064c565b604051808273ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16815260200191505060405180910390f35b34156101e857fe5b6101f0610672565b6040518082815260200191505060405180910390f35b6000600460003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff1681526020019081526020016000205490505b90565b6000600360003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff1681526020019081526020016000205482111561029c57610000565b81600360003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff1681526020019081526020016000206000828254039250508190555081600460003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff168152602001908152602001600020600082825401925050819055507f8e6a0e3d936bdc1a616604a2839199af908a74412516eed5bf14d3416be8f5593383604051808373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff1681526020018281526020019250505060405180910390a15b919050565b6000600360008473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff168152602001908152602001600020548211156103f557610000565b3373ffffffffffffffffffffffffffffffffffffffff16316000548302111561041d57610000565b81600360003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff1681526020019081526020016000206000828254019250508190555081600360008573ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff168152602001908152602001600020600082825403925050819055507fd0c183be209f70036b50de16805d88249019e1288d7b77ef877710999c0d08e6338484604051808473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff1681526020018373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff168152602001828152602001935050505060405180910390a15b92915050565b600081600260003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff1681526020019081526020016000206000828254019250508190555081600360003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16815260200190815260200160002060008282540192505081905550600360003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff1681526020019081526020016000205490505b919050565b600060005490505b90565b600160009054906101000a900473ffffffffffffffffffffffffffffffffffffffff1681565b6000600360003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff1681526020019081526020016000205490505b905600a165627a7a72305820e1f0d1a35a5dc406856d4b41addeb7af724b6ae6c8646b69e6573e2c5254bee70029"

# Read CSV file
def read_csv():
    try:
        with open(FILE) as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            for row in reader:
                DATA = list(reader)
            return DATA
    except Exception as e:
        print("Fail to read CSV {0}".format(e))
        exit(1)

# Start mining
def start_mining(WEB3):
    try:
        if MINE_STATUS != True:
            WEB3.miner.start(1)
    except Exception as e:
        print("Fail to start mining {0}".format(e))
        exit(1)

# Get energy balance
def energy_balance():
    try:
        BALANCE = CONTRACT.call({'from': COINBASE}).getEnergyBalance()
        return BALANCE
    except Exception as e:
        print("Fail to get balance {0}".format(e))
        exit(1)

# Deploy a contract
def deploy_contract(WEB3):
    contract_factory = WEB3.eth.contract(abi = ABI, bytecode = BYTECODE)
    try:
        contract_factory.deploy()
    except Exception as e:
        print("Fail to deploy contract {0}".format(e))
        exit(1)

# Execute setProduction
def set_production(DATA):
    a = 0
    try:
        for row in DATA:
            CONTRACT.transact({'from': COINBASE}).setProduction(int(float(DATA[a][2])))
            a = a + 1
            print(energy_balance())
            time.sleep(60)
    except Exception as e:
        print("Fail to start mining {0}".format(e))
        exit(1)

# Main
if __name__ == "__main__":
    DATA = read_csv()

    start_mining(WEB3)
    #deploy_contract
    set_production(DATA)
