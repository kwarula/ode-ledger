"""
Autonomous Runner for Open Decision Engine.

This module provides a continuous loop that runs the ObserverAgent 
at scheduled intervals while respecting the max_actions_per_day limit 
defined in the autonomy rules.
"""
import os
import time
import yaml
import logging
from datetime import datetime, date
from dotenv import load_dotenv
from ledger.manager import LedgerManager
from agents.observer.agent import ObserverAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ode-runner')

class AutonomousRunner:
    def __init__(self):
        load_dotenv()
        
        # Load autonomy rules
        with open('config/autonomy_rules.yaml', 'r') as f:
            self.rules = yaml.safe_load(f)
        
        self.max_actions_per_day = self.rules['execution']['max_actions_per_day']
        self.actions_today = 0
        self.current_date = date.today()
        
        # Initialize components
        ledger_file = os.getenv("LEDGER_FILE", "ledger/entries.jsonl")
        schema_file = os.getenv("SCHEMA_FILE", "ledger/schema.json")
        self.ledger = LedgerManager(ledger_file, schema_file)
        self.observer = ObserverAgent("obs_auto", self.ledger)
        
        # Interval between observations (in seconds)
        # With max 3 actions/day, we space them out: 24h / 3 = 8 hours = 28800 seconds
        self.observation_interval = 28800  # 8 hours
        
        logger.info(f"Autonomous Runner initialized. Max actions/day: {self.max_actions_per_day}")

    def _reset_daily_counter(self):
        """Reset action counter at midnight."""
        if date.today() != self.current_date:
            self.current_date = date.today()
            self.actions_today = 0
            logger.info("Daily counter reset.")

    def _can_act(self) -> bool:
        """Check if we can perform an action based on daily limits."""
        self._reset_daily_counter()
        return self.actions_today < self.max_actions_per_day

    def run_cycle(self):
        """Run a single observation cycle."""
        if not self._can_act():
            logger.warning(f"Daily limit reached ({self.max_actions_per_day}). Waiting for tomorrow.")
            return False
        
        logger.info("Starting observation cycle...")
        try:
            entry = self.observer.observe()
            if entry:
                self.actions_today += 1
                logger.info(f"Cycle complete. Actions today: {self.actions_today}/{self.max_actions_per_day}")
                return True
        except Exception as e:
            logger.error(f"Error during observation: {e}")
        return False

    def run_forever(self):
        """Main autonomous loop."""
        logger.info("=== Open Decision Engine - Autonomous Mode ===")
        logger.info(f"Observation interval: {self.observation_interval}s ({self.observation_interval/3600:.1f} hours)")
        
        while True:
            self.run_cycle()
            
            # Calculate time until next run
            wait_time = self.observation_interval
            if not self._can_act():
                # If we've hit the limit, wait until midnight
                now = datetime.now()
                tomorrow = datetime.combine(date.today(), datetime.min.time()) + timedelta(days=1)
                wait_time = (tomorrow - now).seconds + 60  # Add 1 min buffer
                logger.info(f"Waiting {wait_time/3600:.1f} hours until midnight reset.")
            
            logger.info(f"Next observation in {wait_time/60:.0f} minutes. Sleeping...")
            time.sleep(wait_time)


if __name__ == "__main__":
    from datetime import timedelta
    runner = AutonomousRunner()
    runner.run_forever()
