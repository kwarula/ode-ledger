import os
import requests
import trafilatura
from typing import List, Dict, Any
from openai import OpenAI
from ledger.manager import LedgerManager

class ObserverAgent:
    def __init__(self, agent_id: str, ledger_manager: LedgerManager):
        self.agent_id = agent_id
        self.ledger_manager = ledger_manager
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def observe(self, target_url: str = "https://www.technologyreview.com/topic/artificial-intelligence/"):
        """
        Fetches content from a URL, summarizes it using OpenAI, 
        and logs the observation to the ledger.
        """
        print(f"[{self.agent_id}] Observing: {target_url}")
        
        # 1. Fetch and extract content with User-Agent
        import requests
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            response = requests.get(target_url, headers=headers, timeout=10)
            response.raise_for_status()
            content = trafilatura.extract(response.text)
        except Exception as e:
            print(f"[{self.agent_id}] Failed to fetch content: {e}")
            content = None
        
        if not content:
            print(f"[{self.agent_id}] No content extracted. Using fallback observation.")
            content = "Autonomous engine heartbeat: Monitoring AI developments."

        # 2. Use LLM to structure the observation
        print(f"[{self.agent_id}] Processing intelligence with OpenAI...")
        prompt = f"""
        Analyze the following text extracted from {target_url} and produce a structured observation report for an autonomous AI ledger.
        
        Text:
        {content[:4000]}  # Limit to 4k chars for prompt safety
        
        Format the output as a JSON object with:
        - "findings": a list of objects with "title" and "impact" (high/medium/low)
        - "summary": a 1-2 sentence overview of the most critical development
        - "confidence": a number between 0 and 1 representing your certainty
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={ "type": "json_object" }
            )
            import json
            raw_payload = json.loads(response.choices[0].message.content)
            
            observation_payload = {
                "source": target_url,
                "findings": raw_payload.get("findings", []),
                "summary": raw_payload.get("summary", "Intelligence gathered from source.")
            }
            confidence = raw_payload.get("confidence", 0.9)

            # 3. Log to ledger
            entry = self.ledger_manager.add_entry(
                agent_id=self.agent_id,
                entry_type="OBSERVATION",
                payload=observation_payload,
                confidence=confidence,
                references=[target_url]
            )
            
            print(f"[{self.agent_id}] Logged real intelligence: {entry.id}")
            return entry
        except Exception as e:
            print(f"[{self.agent_id}] Error processing with OpenAI: {e}")
            return None
