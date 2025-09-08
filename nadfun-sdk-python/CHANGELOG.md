# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.3] - 2024-08-31

### Changed
- **Code Structure Refactoring**
  - Moved common utility functions from `stream/utils/event_parser.py` to `stream/utils.py`
  - Simplified module structure by removing unnecessary nested folders
  - Improved code organization for better maintainability

### Removed
- **Legacy Code Cleanup**
  - Removed unused dataclass-based event classes (`BaseEvent`, `BuyEvent`, `SellEvent`, `SwapEvent`)
  - Deleted `stream/utils/event_parser.py` as it was not being used
  - Cleaned up redundant imports and exports in `__init__.py` files

### Fixed
- **Import Issues**
  - Fixed missing imports for `CurveIndexer` and `DexIndexer` in main `__init__.py`
  - Corrected stream module exports to properly expose all public APIs
  - Ensured all exported items in `__all__` are actually imported

### Improved
- **Code Quality**
  - Added common utility functions (`extract_address_from_topic`, `parse_log_data`, `format_tx_hash`)
  - Reduced code duplication in indexer modules
  - Better type consistency across the SDK

## [0.1.2] - 2024-08-30

### Added
- Historical event indexing with `CurveIndexer` and `DexIndexer`
- Real-time event streaming with `CurveStream` and `DexStream`
- TypedDict-based event types for better type hints

### Changed
- Improved event handling and parsing
- Better WebSocket connection management

## [0.1.1] - 2024-08-29

### Added
- Token operations module for ERC-20 interactions
- Bonding curve query methods

### Fixed
- Gas estimation improvements
- Transaction handling edge cases

## [0.1.0] - 2024-08-28

### Added
- Initial release
- Core trading functionality (buy/sell)
- Basic token operations
- Slippage calculation utilities
- Async/await support throughout