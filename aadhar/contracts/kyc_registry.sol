// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract KYCRegistry {
    struct Record {
        string kycId;
        bytes32 kycHash;
        uint256 timestamp;
    }

    mapping(string => Record) private records;

    event KYCRegistered(string kycId, bytes32 kycHash, uint256 timestamp);

    function registerKYC(string memory _kycId, bytes32 _kycHash) public {
        records[_kycId] = Record(_kycId, _kycHash, block.timestamp);
        emit KYCRegistered(_kycId, _kycHash, block.timestamp);
    }

    function getKYC(string memory _kycId) public view returns (Record memory) {
        return records[_kycId];
    }
}
