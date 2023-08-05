// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.18;

contract Main {
    address private owner;

    enum Mark { add, minus } Mark private mark;

    struct Payment {
        Mark mark;
        address addr;
        uint amount;
        uint timestamp;
    }

    struct Balance {
        uint value;
        uint totalPayments;
        mapping (uint => Payment) payments;
    }

    mapping (address => Balance) private balances;

    event Transaction(address indexed _addr, uint _amount, Mark _mark, uint _timestamp);

    constructor() {
        owner = msg.sender;
    }

    receive() external payable {
        buy();
    }

    modifier lowBalance(uint _amount) {
        require(balances[msg.sender].value > _amount, "Balance too low");
        _;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "You are not owner!");
        _;
    }

    function buy() public payable {
        operationAlloying(msg.sender, msg.value, Mark.add);
    }

    function sell(uint _amount) public lowBalance(_amount) {
        operationAlloying(msg.sender, _amount, Mark.minus);
        payable(msg.sender).transfer(_amount);
    }

    function transferTo(address payable _to, uint _amount) external lowBalance(_amount) {
        operationAlloying(msg.sender, _amount, Mark.minus);
        operationAlloying(_to, _amount, Mark.add);
        _to.transfer(_amount);
    }

    function operationAlloying(address _addr, uint _amount, Mark _mark) internal {
        uint _paymentReceiverNum = balances[_addr].totalPayments;

        if (_mark == Mark.add) {
            balances[_addr].value += _amount;
        }
        else {
            balances[_addr].value -= _amount;
        }

        balances[_addr].totalPayments++;

        Payment memory newReceiverPayment = Payment(
            _mark,
            _addr,
            _amount,
            block.timestamp
        );

        balances[_addr].payments[_paymentReceiverNum] = newReceiverPayment;
        emit Transaction(_addr, _amount, _mark, block.timestamp);
    }

    function withdraw() external onlyOwner {
        operationAlloying(msg.sender, address(this).balance, Mark.minus);
        payable(msg.sender).transfer(address(this).balance);
    }

    function getPayment(address _addr, uint _index) public view returns(Payment memory) {
        return balances[_addr].payments[_index];
    }

    function getBalance(address _addr) public view returns(uint) {
        return balances[_addr].value;
    }
}