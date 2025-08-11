# AST analysis

Get ast from solc via:

```sh
solc --combined-json ast --include-paths=lib --base-path=. <contract-path.sol>
```

or use forge build

```sh
forge build --json --ast --no-cache <contract-name.sol>
```

```sh
forge build
```

## Solc: AST components

1. `contracts`: A mapping of contractpath + contract name

```json
{
  "contracts": {
    "solmate/src/auth/Owned.sol:Owned": {},
    "src/ERC6909.sol:ERC6909": {},
    "src/ERC6909Claims.sol:ERC6909Claims": {},
    "src/Extsload.sol:Extsload": {},
    ...
    }
    "sourceList": [],
    "source": {},
    "version": ""
}
```

2.`sourceList`: an array of all the contracts

```json
{
    "contracts": {},
    "sourceList": [
        "solmate/src/auth/Owned.sol",
        "src/ERC6909.sol",
        "src/ERC6909Claims.sol",
        "src/Extsload.sol",
        "src/Exttload.sol",
        "src/NoDelegateCall.sol",
        ...
    ],
    "sources": {},
    "version": ""
}
```

3.`sources`: an array of all the contracts

```json
{
    "contracts": {},
    "sourceList": [],
    "sources": {
        "solmate/src/auth/Owned.sol": {
          "AST": {
            "absolutePath": "solmate/src/auth/Owned.sol",
            "exportedSymbols": {
              "Owned": [
                7132
              ]
            },
            "id": 7133,
            "license": "AGPL-3.0-only",
            "nodeType": "SourceUnit",
            "nodes": [
              {
                "id": 7074,
                "literals": [
                  "solidity",
                  ">=",
                  "0.8",
                  ".0"
                ],
                "nodeType": "PragmaDirective",
                "src": "42:24:0"
              },
        },
        "id": 1  
        },
        "file2": {
            "AST": {}
            "id": 2
        },
    },
    "version": ""
}
```

4. `version`: the solidity version used to compile the project

```json
{
    "contracts": {},
    "sourceList": [],
    "sources": {},
    "version": "0.8.26+commit.8a97fa7a.Darwin.appleclang"
}
```

## Foundry AST components

1. `build_info`: List of build info

```json
{
    "build_infos": [
        {
            "id": "b9be3347c549e290",
            "source_id_to_path": {
                "0": "lib/solmate/src/auth/Owned.sol",
                "1": "src/ERC6909.sol",
                "2": "src/ERC6909Claims.sol",
                "3": "src/Extsload.sol",
                "4": "src/Exttload.sol",
            }
        },
        "language": "Solidity"
    ]
    
  "contracts": {
    "/User/me/Developer/uniswap/v4-core/lib/solmate/src/auth/Owned.sol": {
      "Owned": [
        {
          "contract": {
            "abi": [
              {
        }],
    }}]}},
    "sources": {},
    "errors": []
}
```

## Go to Definition

- In a node, the reference key looks like `"referencedDeclaration": 1736`
- Go to the id `1736`
- In node `1736` you can look for `"nameLocation": "16944:24:6"`
- `16944` is the byte offset in the file `6` in sources ast mapping

## Example use cases

Go to both `Pool` and `State` declarations.

```json
"valueType": {
  "id": 650,
  "nodeType": "UserDefinedTypeName",
  "pathNode": {
    "id": 649,
    "name": "Pool.State",
    "nameLocations": [
      "5243:4:6",
      "5248:5:6"
    ],
    "nodeType": "IdentifierPath",
    "referencedDeclaration": 4805,
    "src": "5243:10:6"
  },
```
