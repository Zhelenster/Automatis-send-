import json
import base64
import requests
from cosmospy_protobuf import Transaction

with open("wallet.json") as f:
    wallet = json.load(f)

RPC = wallet["rpc"]
ADDR = wallet["address"]
PK = base64.b64decode(wallet["private_key"])

def get_balance(address):
    url = f"{RPC}cosmos/bank/v1beta1/balances/{address}"
    r = requests.get(url)
    coins = r.json().get("balances", [])
    for c in coins:
        if c["denom"] == "uoctra":
            return int(c["amount"]) / 1_000_000
    return 0

def get_account_data(address):
    r = requests.get(f"{RPC}cosmos/auth/v1beta1/accounts/{address}")
    acc = r.json()["account"]
    return int(acc["account_number"]), int(acc["sequence"])

def send_tx(to_address, amount_uoctra, acc_num, seq):
    tx = Transaction(
        privkey=PK,
        account_num=acc_num,
        sequence=seq,
        fee=2000,
        gas=200000,
        memo="Batch OCTRA",
        chain_id="octra_420-1",
    )
    tx.add_transfer(recipient=to_address, amount=amount_uoctra, denom="uoctra")
    signed_tx = tx.get_pushable()
    res = requests.post(f"{RPC}cosmos/tx/v1beta1/txs", json={"tx_bytes": signed_tx, "mode": "BROADCAST_MODE_SYNC"})
    return res.json()

print(f"🔐 Wallet: {ADDR}")
balance = get_balance(ADDR)
print(f"💰 Saldo: {balance:.6f} OCTRA")

amount = float(input("💸 Jumlah OCTRA per address: "))
send_amount = int(amount * 1_000_000)

with open("recipients.txt") as f:
    recipients = [line.strip() for line in f if line.strip()]

acc_num, seq = get_account_data(ADDR)

for i, to_addr in enumerate(recipients):
    print(f"➡️  [{i+1}/{len(recipients)}] Kirim ke {to_addr} ...")
    result = send_tx(to_addr, send_amount, acc_num, seq)
    seq += 1

    if "tx_response" in result:
        code = result["tx_response"].get("code", 0)
        txhash = result["tx_response"].get("txhash", "N/A")
        if code == 0:
            print(f"✅  Sukses | TX: https://octrascan.io/tx/{txhash}")
        else:
            print(f"❌  Gagal | Code: {code} | TX: {txhash}")
    else:
        print("⚠️  Error:", result)
