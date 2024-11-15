import Web3Wallet from "@walletconnect/web3wallet";

export const initWalletConnect = async () => {
  try {
    const wallet = await Web3Wallet.init({
      projectId: "6305a12c5a256339af426208e1677894", // Make sure this is a valid projectId
      logger: 'debug', // Add logger if required
      relayUrl: 'wss://relay.walletconnect.org', // You might need to specify the relay URL
    });

    return wallet;
  } catch (error) {
    console.error("Failed to initialize WalletConnect:", error);
    throw error;
  }
};

export const createSession = async (wallet) => {
  try {
    const session = await wallet.createSession({
      chainId: 1, // Ethereum Mainnet
      metadata: {
        name: "My Vista DApp",
        description: "My DApp Vista Wallet connect",
        url: "https://my-dapp.com",
        icons: ["https://my-dapp.com/icon.png"],
      },
    });

    return session;
  } catch (error) {
    console.error("Failed to create session:", error);
    throw error;
  }
};

export const approveSession = async (wallet, proposal) => {
  const namespaces = {
    eip155: {
      methods: ["eth_sendTransaction", "personal_sign"],
      chains: ["eip155:1"],
      accounts: ["eip155:1:0x..."],
      events: ["chainChanged", "accountsChanged"],
    },
  };

  try {
    await wallet.approveSession({
      id: proposal.id,
      namespaces,
    });
  } catch (error) {
    console.error("Failed to approve session:", error);
    throw error;
  }
};
