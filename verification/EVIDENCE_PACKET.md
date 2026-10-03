# Evidence packet

- Contract: [`0x314BcBB694e3C9e6D2A97F2f4Ee3616e8bDf54c1`](https://explorer-studio.genlayer.com/address/0x314BcBB694e3C9e6D2A97F2f4Ee3616e8bDf54c1)
- Source parity: SHA-256 `2d52099902646aa3fc713f135ba5724ae4e8060d81c73303152a348409b48e39`
- Version: `counterparty-grounded-refund-escrow-v3`
- Policy: immutable commit `3265c1fb560d56549039952eb1ab66b23348380b`; bounded digest `0e0594441a4514e9867fc7d81608073d23eeb314c44f29dcf9036513566fd8b2`
- Actors: merchant `0x736A…c8bB`; buyer `0xA63D…eDBE`; deployer did not perform test roles.

## Quick reviewer path

1. Open contract and confirm version 3.
2. Open happy adjudication [`0x4c9a…d388`](https://explorer-studio.genlayer.com/tx/0x4c9a0ae4363d6d656808700cdaa0f01a13cfbbadd1fad181d0c4b7a71d25d388): consensus returns semantic coverage; readback derives eligible.
3. Open happy settlement [`0x4dda…99f8`](https://explorer-studio.genlayer.com/tx/0x4dda138d6cf25110ab5bad0b563393f39ad9093fc294342c6d3de407285099f8): one native message sends exact escrow to buyer.
4. Open usage-veto settlement [`0x10ba…5cee`](https://explorer-studio.genlayer.com/tx/0x10ba642d647e2dace130a48f049fa032393f3a6c7a20934278c97c07a2a25cee): despite semantic `COVERED`, usage 1 makes the contract release exact escrow to merchant.
5. Inspect `E2E_V3.md` and both machine-readable JSON journals for every guard, return and post-state.

Local gates: 9 direct GenVM tests passed, GenVM lint passed three checks, production frontend build passed. Live claims are limited to the listed transactions and readbacks.
