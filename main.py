import os
from dotenv import load_dotenv
from ledger.manager import LedgerManager
from agents.observer.agent import ObserverAgent

def main():
    load_dotenv()
    
    ledger_file = os.getenv("LEDGER_FILE", "ledger/entries.jsonl")
    schema_file = os.getenv("SCHEMA_FILE", "ledger/schema.json")
    
    print("--- Open Decision Engine Starting ---")
    
    # Initialize components
    ledger = LedgerManager(ledger_file, schema_file)
    observer = ObserverAgent("obs_01", ledger)
    
    # Run initial cycle
    observer.observe()
    
    print(f"Total entries in ledger: {len(ledger.get_all_entries())}")
    print("--- Cycle Complete ---")

if __name__ == "__main__":
    main()
