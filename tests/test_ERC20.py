from collections import OrderedDict

import pytest

from brownie import ERC20, accounts, Contract, reverts
from brownie.network import gas_price
from brownie.network.account import Account
from brownie.network.gas.strategies import LinearScalingStrategy


@pytest.fixture
def token() -> Contract:
    gas_price(LinearScalingStrategy("60 gwei", "70 gwei", 1.1))
    return ERC20.deploy('MAXToken', 'MAX', 1e20, {'from': accounts[0]})


@pytest.fixture(scope='function')
def account(request) -> Account:
    return accounts[request.param]


class TestERC20:
    name = 'MAXToken'
    symbol = 'MAX'
    total_supply = int(1e20)
    zero_address = Account('0x0000000000000000000000000000000000000000')

    def test_signatures_contract(self, token: Contract):
        assert list(token.signatures.keys()) == [
            'allowance',
            'approve',
            'balanceOf',
            'burn',
            'decimals',
            'mint',
            'name',
            'sell',
            'symbol',
            'totalSupply',
            'transfer',
            'transferFrom'
        ]

    def test_name(self, token: Contract):
        assert token.name() == 'MAXToken'

    def test_symbol(self, token: Contract):
        assert token.symbol() == 'MAX'

    def test_decimals(self, token: Contract):
        assert token.decimals() == 18

    def test_totalSupply(self, token: Contract):
        assert token.totalSupply() == self.total_supply

    def test_balanceOf(self, token: Contract):
        assert token.balanceOf(accounts[0]) == 0

    @pytest.mark.parametrize('amount', [1, 1000, int(1e18)])
    def test_receive(self, token: Contract, amount: int):
        tx = accounts[0].transfer(Account(token.address), amount)
        assert token.balanceOf(accounts[0]) == amount

    def test_revert_receive(self, token: Contract):
        with reverts('not enough funds!'):
            tx = accounts[0].transfer(Account(token.address), 0)

    @pytest.mark.parametrize(
        'buy, sell, balance',
        [
            (100, 50, 50),
            (100, 100, 0),
        ]
    )
    def test_sell(self, token: Contract, buy: int, sell: int, balance: int):
        tx = accounts[0].transfer(Account(token.address), buy)
        assert token.balanceOf(accounts[0]) == buy
        tx = token.sell(sell, {'from': accounts[0]})
        assert token.balanceOf(accounts[0]) == balance

    def test_revert_sell_no_cash(self, token: Contract):
        with reverts('not enough tokens!'):
            tx = token.sell(100, {'from': accounts[0]})

    def test_revert_sell_zero_amount(self, token: Contract):
        tx = accounts[0].transfer(Account(token.address), 100)
        assert token.balanceOf(accounts[0]) == 100
        with reverts('amount is zero!'):
            tx = token.sell(0, {'from': accounts[0]})

    @pytest.mark.parametrize(
        'buy, send',
        [
            (1000, 500),
            (1000, 1000),
            (1000, 1),
        ]
    )
    def test_transfer(self, token: Contract, buy: int, send: int):
        tx = accounts[0].transfer(Account(token.address), buy)
        assert token.balanceOf(accounts[0]) == buy
        tx = token.transfer(accounts[1], send, {'from': accounts[0]})
        assert token.balanceOf(accounts[1]) == send
        assert token.balanceOf(accounts[0]) == buy - send

    def test_transfer_no_cash(self, token: Contract):
        with reverts('not enough tokens!'):
            tx = token.transfer(accounts[1], 100, {'from': accounts[0]})

    def test_transfer_zero_amount(self, token: Contract):
        tx = accounts[0].transfer(Account(token.address), 100)
        assert token.balanceOf(accounts[0]) == 100
        with reverts('amount is zero!'):
            tx = token.transfer(accounts[1], 0, {'from': accounts[0]})

    def test_allowance(self, token: Contract):
        assert token.allowance(Account(token.address), accounts[1]) == 0

    @pytest.mark.parametrize(
        'amount',
        [
            1,
            10,
            90000
        ]
    )
    def test_approve(self, token: Contract, amount: int):
        tx = token.approve(accounts[0], amount, {'from': accounts[0]})
        assert token.allowance(accounts[0], accounts[0]) == amount

    @pytest.mark.parametrize(
        'amount',
        [
            1,
            100,
        ]
    )
    def test_transferFrom(self, token: Contract, amount: int):
        tx = accounts[0].transfer(Account(token.address), amount)
        assert token.balanceOf(accounts[0]) == amount
        tx = token.approve(accounts[1], amount, {'from': accounts[0]})
        assert token.allowance(accounts[0], accounts[1]) == amount
        tx = token.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})
        assert token.balanceOf(accounts[2]) == amount

    def test_trasferFrom_no_appove(self, token: Contract):
        tx = accounts[0].transfer(Account(token.address), 100)
        assert token.balanceOf(accounts[0]) == 100
        with reverts('no allowance!'):
            tx = token.transferFrom(accounts[0], accounts[2], 100, {'from': accounts[1]})

    def test_transferFrom_no_cash(self, token: Contract):
        with reverts('not enough tokens!'):
            tx = token.transferFrom(accounts[0], accounts[2], 100, {'from': accounts[1]})

    def test_transferFrom_zero_amount(self, token: Contract):
        tx = accounts[0].transfer(Account(token.address), 100)
        assert token.balanceOf(accounts[0]) == 100
        tx = token.approve(accounts[1], 100, {'from': accounts[0]})
        assert token.allowance(accounts[0], accounts[1]) == 100
        with reverts('amount is zero!'):
            tx = token.transferFrom(accounts[0], accounts[2], 0, {'from': accounts[1]})

    @pytest.mark.parametrize(
        'amount',
        [
            1,
            100,
        ]
    )
    def test_mint(self, token: Contract, amount: int):
        token.mint(amount, {'from': accounts[0]})
        assert token.totalSupply() == self.total_supply + amount

    def test_mint_not_owner(self, token: Contract):
        with reverts('not an owner!'):
            token.mint(10000, {'from': accounts[1]})

    @pytest.mark.parametrize(
        'amount',
        [
            1,
            100
        ]
    )
    def test_burn(self, token: Contract, amount: int):
        tx = accounts[0].transfer(Account(token.address), amount)
        assert token.balanceOf(accounts[0]) == amount
        tx = token.burn(accounts[0], amount)
        assert token.totalSupply() == self.total_supply - amount
        assert token.balanceOf(accounts[0]) == 0

    def test_burn_not_owner(self, token: Contract):
        tx = accounts[0].transfer(Account(token.address), 100)
        assert token.balanceOf(accounts[0]) == 100
        with reverts('not an owner!'):
            tx = token.burn(accounts[0], 99, {'from': accounts[1]})

    def test_burn_no_cash(self, token: Contract):
        with reverts('not enough tokens!'):
            tx = token.burn(accounts[0], 100, {'from': accounts[0]})

    def test_burn_zero_amount(self, token: Contract):
        tx = accounts[0].transfer(Account(token.address), 100)
        assert token.balanceOf(accounts[0]) == 100
        with reverts('amount is zero!'):
            tx = token.burn(accounts[0], 0, {'from': accounts[0]})
