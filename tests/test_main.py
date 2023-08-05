from collections import OrderedDict

import pytest

from brownie import accounts, config, Main, chain, reverts
from brownie.network import gas_price
from brownie.network.gas.strategies import LinearScalingStrategy


@pytest.fixture
def contract():
    gas_strategy = LinearScalingStrategy("60 gwei", "70 gwei", 1.1)
    gas_price(gas_strategy)
    return Main.deploy({'from': accounts[0]})


@pytest.fixture
def owner():
    return accounts[0]


@pytest.fixture
def address():
    return accounts[1]


class TestClass:
    amounts = [0, 1, 1000, 1e18]

    def test_getBalance(self, contract, owner):
        assert contract.getBalance(owner) == 0

    @pytest.mark.parametrize('amount', amounts)
    def test_buy(self, contract, owner, amount):
        contract.buy({'from': owner, 'amount': amount})
        assert contract.getBalance(owner) == amount

    @pytest.mark.parametrize('amount', amounts)
    def test_getPayment(self, contract, owner, amount):
        contract.buy({'from': owner, 'amount': amount})
        tx2 = contract.getPayment(owner, 0, {'from': owner})
        assert tx2[:-1] == (0, owner, amount)

    @pytest.mark.parametrize('buy, sell, result', [
        (1, 0, 1), (1000, 500, 500), (90000, 1, 89999)
    ])
    def test_sell(self, contract, owner, buy, sell, result):
        contract.buy({'from': owner, 'amount': buy})
        contract.sell(sell, {'from': owner})
        assert contract.getBalance(owner) == result

    @pytest.mark.parametrize('buy, transfer, owner_result, account_result', [
        (2, 1, 1, 1), (100, 99, 1, 99), (100, 0, 100, 0)
    ])
    def test_transferTo(self, contract, owner, buy, transfer, owner_result, account_result, address):
        contract.buy({'from': owner, 'amount': buy})
        contract.transferTo(address, transfer)
        assert contract.getBalance(owner) == owner_result
        assert contract.getBalance(address) == account_result

    @pytest.mark.parametrize('amount', amounts)
    def test_withdraw(self, contract, owner, amount):
        contract.buy({'from': owner, 'amount': amount})
        contract.withdraw({'from': owner})
        assert contract.getBalance(owner) == 0

    @pytest.mark.parametrize('amount', amounts)
    def test_onlyOwner_revert(self, contract, owner, amount, address):
        with reverts('You are not owner!'):
            contract.buy({'from': owner, 'amount': amount})
            contract.withdraw({'from': address})

    @pytest.mark.parametrize('amount', amounts)
    def test_lowBalance_revert(self, contract, owner, amount):
        with reverts('Balance too low'):
            contract.sell(amount, {'from': owner})

    @pytest.mark.parametrize('amount', amounts)
    def test_lowBalance_transfer(self, contract, address, amount):
        with reverts('Balance too low'):
            contract.transferTo(address, amount)

    @pytest.mark.parametrize('amount', amounts)
    def test_Transaction_event(self, contract, owner, amount):
        tx = contract.buy({'from': owner, 'amount': amount})
        event = OrderedDict({'_addr': owner, '_amount': amount, '_mark': 0, '_timestamp': chain.time()})
        assert tx.events['Transaction'] == event
