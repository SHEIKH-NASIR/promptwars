"""
generator.py - Synthetic Indian Banking Transaction Generator
Generates realistic fictional financial records for FinGuard AI.
Supports UPI, IMPS, NEFT, RTGS, Bank Transfers, Mobile Wallets.
Implements 8 controlled scenarios with reproducible seeds.
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from pathlib import Path
import pandas as pd
from faker import Faker

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

INDIAN_CITIES = [
    "Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Ahmedabad",
    "Chennai", "Kolkata", "Pune", "Jaipur", "Surat",
    "Lucknow", "Kanpur", "Nagpur", "Indore", "Thane",
    "Bhopal", "Visakhapatnam", "Pimpri-Chinchwad", "Patna", "Vadodara"
]

MERCHANT_CATEGORIES = [
    "Groceries & Supermarkets", "Dining & Food Delivery", "Electronics & Gadgets",
    "Clothing & Apparel", "Peer-to-Peer Transfer", "Utilities & Bills",
    "Travel & Transport", "Entertainment & Gaming", "Cryptocurrency & Forex",
    "Jewelry & Luxury Goods", "Healthcare & Pharmacy", "Cash Withdrawal (Micro-ATM)"
]

PAYMENT_METHODS = ["UPI", "IMPS", "NEFT", "RTGS", "Bank Transfer", "Mobile Wallet"]

BANK_PREFIXES = ["HDFC", "SBIN", "ICIC", "AXIS", "KKBK", "PUNB", "BARB", "YESB"]


class TransactionGenerator:
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.fake = Faker("en_IN")
        Faker.seed(seed)
        random.seed(seed)
        self._account_pool = [self._generate_account_number() for _ in range(300)]
        self._device_pool = [f"DEV-{random.randint(100000, 999999)}" for _ in range(150)]

    def _generate_account_number(self, bank: str = None) -> str:
        if not bank:
            bank = random.choice(BANK_PREFIXES)
        return f"{bank}{random.randint(1000000000, 9999999999)}"

    def _generate_fictional_ip(self) -> str:
        # Fictional private or safe synthetic ranges
        return f"10.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"

    def generate_normal_transaction(self, base_time: datetime) -> Dict[str, Any]:
        sender = random.choice(self._account_pool[:200])
        receiver = random.choice([acc for acc in self._account_pool if acc != sender])
        txn_type = random.choices(
            PAYMENT_METHODS, weights=[0.45, 0.20, 0.15, 0.05, 0.10, 0.05]
        )[0]

        # Normal amount distribution (₹50 to ₹15,000)
        if txn_type in ["UPI", "Mobile Wallet"]:
            amount = round(random.lognormvariate(6.2, 0.9), 2)
            amount = max(20.0, min(amount, 45000.0))
        elif txn_type in ["RTGS"]:
            amount = round(random.uniform(200000.0, 500000.0), 2)
        else:
            amount = round(random.lognormvariate(7.5, 1.0), 2)
            amount = max(100.0, min(amount, 80000.0))

        sender_loc = random.choice(INDIAN_CITIES)
        receiver_loc = sender_loc if random.random() < 0.65 else random.choice(INDIAN_CITIES)

        return {
            "transaction_id": f"TXN-{random.randint(10000000, 99999999)}",
            "sender_account": sender,
            "receiver_account": receiver,
            "amount": float(amount),
            "timestamp": base_time.isoformat(),
            "transaction_type": txn_type,
            "merchant_category": random.choice(MERCHANT_CATEGORIES),
            "sender_location": sender_loc,
            "receiver_location": receiver_loc,
            "device_id": random.choice(self._device_pool),
            "ip_address": self._generate_fictional_ip(),
            "transaction_status": random.choices(["SUCCESS", "FAILED"], weights=[0.96, 0.04])[0],
            "fraud_label": 0,
            "scenario_tag": "NORMAL"
        }

    def generate_high_value_spike(self, base_time: datetime) -> List[Dict[str, Any]]:
        """Scenario 2: Unusually high value transfer compared to normal threshold."""
        sender = random.choice(self._account_pool)
        receiver = self._generate_account_number("SBIN")
        amount = round(random.uniform(850000.0, 3500000.0), 2)
        return [{
            "transaction_id": f"TXN-HV-{random.randint(100000, 999999)}",
            "sender_account": sender,
            "receiver_account": receiver,
            "amount": float(amount),
            "timestamp": base_time.isoformat(),
            "transaction_type": random.choice(["RTGS", "NEFT", "Bank Transfer"]),
            "merchant_category": "Jewelry & Luxury Goods",
            "sender_location": random.choice(INDIAN_CITIES),
            "receiver_location": random.choice(INDIAN_CITIES),
            "device_id": random.choice(self._device_pool),
            "ip_address": self._generate_fictional_ip(),
            "transaction_status": "SUCCESS",
            "fraud_label": 1,
            "scenario_tag": "HIGH_VALUE_ANOMALY"
        }]

    def generate_rapid_velocity_burst(self, base_time: datetime) -> List[Dict[str, Any]]:
        """Scenario 3: Rapid repeated transfers from same account within 2-5 minutes."""
        sender = random.choice(self._account_pool)
        receiver = random.choice(self._account_pool)
        device = random.choice(self._device_pool)
        records = []
        burst_count = random.randint(4, 7)
        for i in range(burst_count):
            t = base_time + timedelta(seconds=i * random.randint(15, 45))
            amount = round(random.uniform(15000.0, 35000.0), 2)
            records.append({
                "transaction_id": f"TXN-VEL-{random.randint(100000, 999999)}",
                "sender_account": sender,
                "receiver_account": receiver,
                "amount": float(amount),
                "timestamp": t.isoformat(),
                "transaction_type": "UPI",
                "merchant_category": "Entertainment & Gaming",
                "sender_location": "Mumbai",
                "receiver_location": "Bengaluru",
                "device_id": device,
                "ip_address": self._generate_fictional_ip(),
                "transaction_status": "SUCCESS",
                "fraud_label": 1,
                "scenario_tag": "RAPID_VELOCITY"
            })
        return records

    def generate_multiple_incoming_fanin(self, base_time: datetime) -> List[Dict[str, Any]]:
        """Scenario 4: Multiple accounts sending funds into one collector account within minutes."""
        collector = f"HDFC{random.randint(8000000000, 8999999999)}"
        records = []
        senders = random.sample(self._account_pool, 5)
        for i, s in enumerate(senders):
            t = base_time + timedelta(minutes=i * 3 + random.randint(1, 2))
            amt = round(random.uniform(40000.0, 49000.0), 2)
            records.append({
                "transaction_id": f"TXN-FIN-{random.randint(100000, 999999)}",
                "sender_account": s,
                "receiver_account": collector,
                "amount": float(amt),
                "timestamp": t.isoformat(),
                "transaction_type": "IMPS",
                "merchant_category": "Peer-to-Peer Transfer",
                "sender_location": random.choice(INDIAN_CITIES),
                "receiver_location": "Delhi",
                "device_id": random.choice(self._device_pool),
                "ip_address": self._generate_fictional_ip(),
                "transaction_status": "SUCCESS",
                "fraud_label": 1,
                "scenario_tag": "FAN_IN_AGGREGATION"
            })
        return records

    def generate_rapid_outgoing_fanout(self, base_time: datetime) -> List[Dict[str, Any]]:
        """Scenario 5: Rapid outgoing dispersion from single account to multiple receivers."""
        distributor = f"ICIC{random.randint(7000000000, 7999999999)}"
        receivers = random.sample(self._account_pool, 5)
        records = []
        for i, r in enumerate(receivers):
            t = base_time + timedelta(minutes=i * 2 + 1)
            amt = round(random.uniform(30000.0, 48000.0), 2)
            records.append({
                "transaction_id": f"TXN-FOUT-{random.randint(100000, 999999)}",
                "sender_account": distributor,
                "receiver_account": r,
                "amount": float(amt),
                "timestamp": t.isoformat(),
                "transaction_type": "UPI",
                "merchant_category": "Peer-to-Peer Transfer",
                "sender_location": "Bengaluru",
                "receiver_location": random.choice(INDIAN_CITIES),
                "device_id": random.choice(self._device_pool),
                "ip_address": self._generate_fictional_ip(),
                "transaction_status": "SUCCESS",
                "fraud_label": 1,
                "scenario_tag": "FAN_OUT_DISPERSION"
            })
        return records

    def generate_structuring_scenario(self, base_time: datetime) -> List[Dict[str, Any]]:
        """Scenario 6: Transaction splitting / Structuring to avoid regulatory limits (e.g. ₹50k threshold)."""
        sender = f"AXIS{random.randint(6000000000, 6999999999)}"
        receiver = f"KKBK{random.randint(5000000000, 5999999999)}"
        records = []
        # 4 to 6 transfers of ₹47,000 - ₹49,800 within 45 minutes
        num_splits = random.randint(4, 6)
        for i in range(num_splits):
            t = base_time + timedelta(minutes=i * 6 + random.randint(1, 3))
            amt = round(random.uniform(47500.0, 49850.0), 2)
            records.append({
                "transaction_id": f"TXN-STR-{random.randint(100000, 999999)}",
                "sender_account": sender,
                "receiver_account": receiver,
                "amount": float(amt),
                "timestamp": t.isoformat(),
                "transaction_type": "IMPS",
                "merchant_category": "Peer-to-Peer Transfer",
                "sender_location": "Surat",
                "receiver_location": "Ahmedabad",
                "device_id": random.choice(self._device_pool),
                "ip_address": self._generate_fictional_ip(),
                "transaction_status": "SUCCESS",
                "fraud_label": 1,
                "scenario_tag": "STRUCTURING"
            })
        return records

    def generate_mule_account_scenario(self, base_time: datetime) -> List[Dict[str, Any]]:
        """Scenario 7: Mule Account - Receives funds from 3 accounts and rapidly drains 95%+ to another."""
        mule = f"SBIN{random.randint(4000000000, 4999999999)}"
        victims = random.sample(self._account_pool, 3)
        offshore_dest = f"BARB{random.randint(3000000000, 3999999999)}"
        records = []

        total_in = 0.0
        # Inflows
        for i, v in enumerate(victims):
            t = base_time + timedelta(minutes=i * 5)
            amt = round(random.uniform(60000.0, 95000.0), 2)
            total_in += amt
            records.append({
                "transaction_id": f"TXN-MULE-IN-{random.randint(100000, 999999)}",
                "sender_account": v,
                "receiver_account": mule,
                "amount": float(amt),
                "timestamp": t.isoformat(),
                "transaction_type": "NEFT",
                "merchant_category": "Peer-to-Peer Transfer",
                "sender_location": random.choice(INDIAN_CITIES),
                "receiver_location": "Kolkata",
                "device_id": random.choice(self._device_pool),
                "ip_address": self._generate_fictional_ip(),
                "transaction_status": "SUCCESS",
                "fraud_label": 1,
                "scenario_tag": "MULE_ACCOUNT_IN"
            })

        # Outflow drain 12 minutes later
        drain_time = base_time + timedelta(minutes=22)
        drain_amount = round(total_in * random.uniform(0.94, 0.98), 2)
        records.append({
            "transaction_id": f"TXN-MULE-OUT-{random.randint(100000, 999999)}",
            "sender_account": mule,
            "receiver_account": offshore_dest,
            "amount": float(drain_amount),
            "timestamp": drain_time.isoformat(),
            "transaction_type": "RTGS",
            "merchant_category": "Cryptocurrency & Forex",
            "sender_location": "Kolkata",
            "receiver_location": "Mumbai",
            "device_id": random.choice(self._device_pool),
            "ip_address": self._generate_fictional_ip(),
            "transaction_status": "SUCCESS",
            "fraud_label": 1,
            "scenario_tag": "MULE_ACCOUNT_DRAIN"
        })
        return records

    def generate_circular_movement_scenario(self, base_time: datetime) -> List[Dict[str, Any]]:
        """Scenario 8: Circular Money Movement: A -> B -> C -> A."""
        acc_a = f"YESB{random.randint(9000000000, 9999999999)}"
        acc_b = f"HDFC{random.randint(9000000000, 9999999999)}"
        acc_c = f"ICIC{random.randint(9000000000, 9999999999)}"

        amount = round(random.uniform(150000.0, 300000.0), 2)
        records = [
            {
                "transaction_id": f"TXN-CIRC-1-{random.randint(100000, 999999)}",
                "sender_account": acc_a,
                "receiver_account": acc_b,
                "amount": float(amount),
                "timestamp": (base_time + timedelta(minutes=5)).isoformat(),
                "transaction_type": "NEFT",
                "merchant_category": "Peer-to-Peer Transfer",
                "sender_location": "Hyderabad",
                "receiver_location": "Pune",
                "device_id": random.choice(self._device_pool),
                "ip_address": self._generate_fictional_ip(),
                "transaction_status": "SUCCESS",
                "fraud_label": 1,
                "scenario_tag": "CIRCULAR_STEP_1"
            },
            {
                "transaction_id": f"TXN-CIRC-2-{random.randint(100000, 999999)}",
                "sender_account": acc_b,
                "receiver_account": acc_c,
                "amount": float(round(amount * 0.98, 2)),
                "timestamp": (base_time + timedelta(minutes=15)).isoformat(),
                "transaction_type": "NEFT",
                "merchant_category": "Peer-to-Peer Transfer",
                "sender_location": "Pune",
                "receiver_location": "Chennai",
                "device_id": random.choice(self._device_pool),
                "ip_address": self._generate_fictional_ip(),
                "transaction_status": "SUCCESS",
                "fraud_label": 1,
                "scenario_tag": "CIRCULAR_STEP_2"
            },
            {
                "transaction_id": f"TXN-CIRC-3-{random.randint(100000, 999999)}",
                "sender_account": acc_c,
                "receiver_account": acc_a,
                "amount": float(round(amount * 0.96, 2)),
                "timestamp": (base_time + timedelta(minutes=28)).isoformat(),
                "transaction_type": "NEFT",
                "merchant_category": "Peer-to-Peer Transfer",
                "sender_location": "Chennai",
                "receiver_location": "Hyderabad",
                "device_id": random.choice(self._device_pool),
                "ip_address": self._generate_fictional_ip(),
                "transaction_status": "SUCCESS",
                "fraud_label": 1,
                "scenario_tag": "CIRCULAR_STEP_3"
            }
        ]
        return records

    def generate_full_dataset(self, total_normal: int = 1500, save_csv: bool = True) -> pd.DataFrame:
        """Generates comprehensive dataset containing all 8 controlled scenarios and normal spend."""
        now = datetime.now()
        start_time = now - timedelta(days=7)
        all_records = []

        # 1. Normal transactions
        for i in range(total_normal):
            rand_delta = timedelta(
                days=random.uniform(0, 7),
                hours=random.uniform(0, 24),
                minutes=random.uniform(0, 60)
            )
            all_records.append(self.generate_normal_transaction(start_time + rand_delta))

        # 2. High value transfers (e.g. 10 instances)
        for i in range(10):
            t = start_time + timedelta(days=i * 0.7, hours=random.randint(10, 18))
            all_records.extend(self.generate_high_value_spike(t))

        # 3. Rapid velocity bursts (e.g. 8 instances)
        for i in range(8):
            t = start_time + timedelta(days=i * 0.8, hours=random.randint(12, 22))
            all_records.extend(self.generate_rapid_velocity_burst(t))

        # 4. Multiple incoming fan-ins (e.g. 6 instances)
        for i in range(6):
            t = start_time + timedelta(days=i * 1.0, hours=random.randint(9, 15))
            all_records.extend(self.generate_multiple_incoming_fanin(t))

        # 5. Rapid outgoing fan-outs (e.g. 6 instances)
        for i in range(6):
            t = start_time + timedelta(days=i * 1.1, hours=random.randint(14, 20))
            all_records.extend(self.generate_rapid_outgoing_fanout(t))

        # 6. Structuring scenarios (e.g. 7 instances)
        for i in range(7):
            t = start_time + timedelta(days=i * 0.9, hours=random.randint(11, 19))
            all_records.extend(self.generate_structuring_scenario(t))

        # 7. Mule account scenarios (e.g. 8 instances)
        for i in range(8):
            t = start_time + timedelta(days=i * 0.8, hours=random.randint(8, 23))
            all_records.extend(self.generate_mule_account_scenario(t))

        # 8. Circular money movements (e.g. 6 instances)
        for i in range(6):
            t = start_time + timedelta(days=i * 1.0, hours=random.randint(10, 16))
            all_records.extend(self.generate_circular_movement_scenario(t))

        df = pd.DataFrame(all_records)
        df["timestamp"] = pd.to_datetime(df["timestamp"], format="mixed", errors="coerce")
        df = df[df["timestamp"].notna()].sort_values("timestamp").reset_index(drop=True)

        if save_csv:
            csv_path = DATA_DIR / "finguard_transactions.csv"
            df.to_csv(csv_path, index=False)
            print(f"Generated {len(df)} transactions and saved to {csv_path}")

        return df


if __name__ == "__main__":
    gen = TransactionGenerator(seed=42)
    df = gen.generate_full_dataset(total_normal=2000)
    print("Dataset distribution:")
    print(df["scenario_tag"].value_counts())
    print("Fraud label breakdown:", df["fraud_label"].value_counts().to_dict())
