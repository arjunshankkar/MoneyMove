# MoneyMove

MoneyMove is the implementation of a blockchain for money transfer, where consensus is achieved using vanilla Paxos. The system is built to sustain despite up to 50% of nodes crash failing. SHA256 is used to ensure block links are secure and not easily attacked maliciously. The system also tolerates network partitioning and supports data persistence by writing relevant data structures on disk.

# TO RUN

1. Ensure you are running python 3.
2. Run network process
3. Run the server processes 5 times, with arguments 0, 1, 2, 3, and 4.
4. Run client.py, and send transactions through this terminal. Also, you can printBlockchain on a specified node to ensure consistency throughout nodes, printBalance to check the remaining balance on all 5 nodes based on current transactions, and printSet, which holds the transactions at that node that have not yet been commited to the blockchain.

Crashing up to two servers (the boundary for 50%) will still have the system functioning properly. The print statements on the servers throughout the process indicate paxos taking place step-by-step, ensuring consensus. 
