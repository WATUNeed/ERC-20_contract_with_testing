from brownie import accounts, config, Main
from brownie.network import gas_price
from brownie.network.gas.strategies import LinearScalingStrategy

gas_strategy = LinearScalingStrategy("60 gwei", "70 gwei", 1.1)

gas_price(gas_strategy)


def deploy_simple_storage():
    owner = accounts[0]
    second = accounts[1]
    contract = owner.deploy(Main)
    contract.receive({'from': owner, 'amount': 1e18})
    contract.transferTo(second, 1e17)
    contract.sell(1e16, {'from': second})


def main():
    deploy_simple_storage()
