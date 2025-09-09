# Telegram DEX Bot Project

## Overview
A sophisticated Telegram bot for decentralized exchange (DEX) trading on Nad.fun platform. The bot enables users to trade tokens on Monad blockchain directly through Telegram with secure wallet management and real-time trading capabilities.

## Current State
✅ **MVP Completed (September 8, 2025)**
- Full bot architecture implemented
- Nad.fun Python SDK integrated
- Database schema and persistence layer ready
- Telegram bot with aiogram framework setup
- Secure wallet management system
- Trading engine with price quotes
- Basic commands implemented (/start, /wallet, /price, etc.)
- Workflow configured and running

## Project Architecture

### Core Components
1. **Telegram Bot** (`bot/telegram_bot.py`)
   - aiogram-based bot handling user interactions
   - Command handlers for wallet and trading operations
   - Inline keyboards for user-friendly interface

2. **Database Manager** (`database/db_manager.py`)
   - SQLite-based persistence with aiosqlite
   - Tables: users, wallets, transactions, orders, configs
   - Async operations with proper error handling

3. **Wallet Manager** (`wallet/wallet_manager.py`)
   - Secure wallet creation and import
   - Private key encryption using Fernet
   - Web3 integration for blockchain operations

4. **Trade Engine** (`trade/trade_engine.py`)
   - Nad.fun SDK integration for DEX operations
   - Buy/sell trade execution
   - Price quotes and token information
   - Slippage and risk management

5. **Configuration** (`config/settings.py`)
   - Centralized bot settings
   - Environment-based configuration
   - Trading parameters and limits

## Features Implemented

### Wallet Management
- Create new wallets with encrypted private keys
- Import existing wallets via private key
- Multi-wallet support per user
- Secure key storage and retrieval

### Trading Core
- Real-time token price quotes via Nad.fun SDK
- Token address validation
- Basic trading command structure
- Integration with Somnia/Monad blockchain

### Security
- Private key encryption using cryptography.fernet
- Non-custodial wallet approach
- Secure database storage
- Environment variable configuration

### User Interface
- Interactive Telegram commands
- Inline keyboard navigation
- Markdown formatting for readability
- Error handling and user feedback

## Technical Stack
- **Backend**: Python 3.11, aiogram, aiosqlite
- **Blockchain**: Web3.py, eth-account, Nad.fun SDK
- **Security**: cryptography (Fernet encryption)
- **Database**: SQLite with async operations
- **Environment**: Replit with workflow management

## Next Development Phases

### Phase 1 Extensions (Immediate)
- Complete buy/sell command implementation
- Transaction status tracking
- Stop-loss and take-profit orders
- Portfolio tracking and P/L calculation

### Phase 2 (Scaling)
- PostgreSQL migration for production
- Redis caching for price data
- Multiple worker support
- Enhanced error handling and retries

### Phase 3 (Advanced)
- Automated trading strategies
- Price alerts and notifications
- Analytics dashboard
- Multi-chain support

## Configuration
- Environment variables in `.env`
- Telegram bot token required
- RPC endpoint for Somnia network
- Encryption keys for wallet security

## Security Considerations
- Private keys never stored in plaintext
- User funds remain non-custodial
- Encrypted local storage only
- Input validation for all operations

## Recent Changes (September 8, 2025)
- Initial project setup and architecture design
- Complete MVP implementation
- Nad.fun SDK integration and testing
- Database schema creation
- Telegram bot framework setup
- Workflow configuration and deployment

## User Preferences
- Secure, non-custodial approach prioritized
- Simple, intuitive Telegram interface
- Real-time trading capabilities
- Comprehensive risk management features

The project is ready for immediate testing and further development based on user feedback and requirements.
