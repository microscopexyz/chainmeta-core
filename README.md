# Chainmeta
**Chainmeta** is the onchain metadata exchange protocol defined by [Microscope Protocol](https://microscopeprotocol.xyz/)

```
>>> import chainmeta
>>> f = open("./examples/coinbase_sample.json")
>>> m = chainmeta.load(f, artifact_base_path="./examples")
>>> m['chainmetadata']['schema']
'https://github.com/openchainmeta/chainmetareader/chainmeta/schemas/artifact_schema.json'
>>> m['chainmetadata']['artifact'][0]
ChainmetaItem(chain='ethereum_mainnet', address='0xf177aa7b0602f787f6f01c65f4b2e267336fd349', entity='uniswap', name='Uniswap V2: Hmf', categories=['defi', 'dex'], source='ground_truth', submitted_by='coinbase', submitted_on='2022-09-21 00:00:00', additional_metadata={})
```

## What is Microsocope?
* [Microscope Whitepaper](https://github.com/microscopexyz/chainmeta-core/blob/main/doc/whitepaper_v1.pdf)
* [Microscope Taxonomy](https://github.com/microscopexyz/chainmeta-core/blob/main/doc/taxonomy.md)
* [Protocol Website](http://microscopeprotocol.xyz/)
