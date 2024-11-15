import React from 'react';
import { useMoralis } from 'react-moralis';
import './App.css';

function WalletConnectComponent() {
  const { authenticate, isAuthenticated, user, logout } = useMoralis();

  const connectWallet = async () => {
    try {
      await authenticate({
        provider: 'walletconnect',
        chainId: 1, // Ethereum Mainnet
        theme: 'dark',
      });
    } catch (e) {
      console.error(e);
    }
  };

  const disconnectWallet = async () => {
    await logout();
  };

  return (
    <div>
      {isAuthenticated ? (
        <div>
          <p>Connected Address: {user.get('ethAddress')}</p>
          <button className="disconnect-button" onClick={disconnectWallet}>
            Disconnect Wallet
          </button>
        </div>
      ) : (
        <button className="connect-button" onClick={connectWallet}>
          Connect Wallet
        </button>
      )}
    </div>
  );
}

export default WalletConnectComponent;
