import React from 'react';
import { MoralisProvider } from 'react-moralis';
import WalletConnectComponent from './WalletConnectComponent';

function App() {
  return (
    <MoralisProvider apiKey="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjI5OGFkNTZkLWJiNGQtNDE5ZS1hYzZjLTY5ZDRjMTM3YmJhOCIsIm9yZ0lkIjoiMzk4MDYwIiwidXNlcklkIjoiNDA5MDIxIiwidHlwZUlkIjoiNjI5MzMxMWUtMDc2Ni00MGFiLTljMmItYWFmOTU4Y2FkZmEyIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3MTk1MDAzMjYsImV4cCI6NDg3NTI2MDMyNn0.blett0fmlYaJrOlfTATFPExEc43LOQmb-JoW7Dp_qfY">
      <WalletConnectComponent />
    </MoralisProvider>
  );
}

export default App;
