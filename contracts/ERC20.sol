// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./IERC20.sol";

contract ERC20 is IERC20 {
    address private _owner;
    string private _name;
    string private _symbol;
    uint256 private _totalSupply;
    mapping (address => uint256) private _balances;
    mapping (address => mapping (address => uint256)) private _allowances;

    constructor (string memory name_, string memory symbol_, uint256 initialSupply) {
        _name = name_;
        _symbol = symbol_;
        _owner = msg.sender;
        mint(initialSupply);
    }

    receive() external payable {
        require(msg.value > 0, "not enough funds!");
        _balances[msg.sender] += msg.value;
    }

    function sell(uint256 amount) external enoughTokens(msg.sender, amount) {
        _balances[msg.sender] -= amount;
        payable(msg.sender).transfer(amount);
    }

    modifier enoughTokens(address from, uint256 amount) {
        require(balanceOf(from) >= amount, "not enough tokens!");
        require(amount > 0, "amount is zero!");
        _;
    }

    modifier onlyOwner() {
        require(msg.sender == _owner, "not an owner!");
        _;
    }

    function name() public view returns (string memory) {
        return _name;
    }

    function symbol() public view returns (string memory) {
        return _symbol;
    }
    
    function decimals() public pure returns (uint8) {
        return 18;
    }

    function totalSupply() public view returns (uint256) {
        return _totalSupply;
    }

    function balanceOf(address account) public view returns (uint256) {
        return _balances[account];
    }

    function transfer(address to, uint256 amount) public enoughTokens(msg.sender, amount) {
        _beforeTokenTransfer(msg.sender, to, amount);
        _balances[msg.sender] -= amount;
        _balances[to] += amount;
        emit Transfer(msg.sender, to, amount);
    }

    function allowance(address owner, address spender) public view returns (uint256) {
        return _allowances[owner][spender];
    }

    function approve(address spender, uint256 amount) public {
        _approve(msg.sender, spender, amount);
    }

    function _approve(address sender, address spender, uint256 amount) internal virtual {
        _allowances[sender][spender] = amount;
        emit Approve(sender, spender, amount);
    }

    function transferFrom(address sender, address recipient, uint256 amount) public enoughTokens(sender, amount) {
        _beforeTokenTransfer(sender, recipient, amount);
        require(_allowances[sender][msg.sender] >= amount, "no allowance!");
        _allowances[sender][msg.sender] -= amount;

        _balances[sender] -= amount;
        _balances[recipient] += amount;
        emit Transfer(sender, recipient, amount);
    }

    function mint(uint256 amount) public onlyOwner {
        _beforeTokenTransfer(address(0), address(this), amount);
        _balances[address(this)] += amount;
        _totalSupply += amount;
        emit Transfer(address(0), address(this), amount);
    }

    function burn(address from, uint256 amount) public onlyOwner enoughTokens(from, amount) {
        require(_totalSupply - amount > 0, "cannot be zero!");
        _beforeTokenTransfer(from, address(0), amount);
        _balances[from] -= amount;
        _totalSupply -= amount;
    }

    function _beforeTokenTransfer(address from, address to, uint256 amount) internal virtual {}
}
