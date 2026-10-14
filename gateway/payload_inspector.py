import os
import re
import time
import hashlib
from typing import Dict, List, Tuple

class PayloadInspector:
    def __init__(self):
        # Read thresholds from environment variables
        self.max_length = int(os.getenv("MAX_PROMPT_LENGTH", "500"))
        self.repetition_threshold = float(os.getenv("REPETITION_THRESHOLD", "0.3"))
        self.risk_threshold = float(os.getenv("RISK_THRESHOLD", "0.7"))
        
        # History of recent prompts to detect duplicate spam: {client_id: [(timestamp, prompt_hash)]}
        self.prompt_history: Dict[str, List[Tuple[float, str]]] = {}

    def inspect(self, client_id: str, prompt: str) -> Tuple[float, List[str]]:
        """
        Inspects the incoming prompt using heuristics.
        Returns:
            - risk_score: float between 0.0 and 1.0+ (where >= risk_threshold is blocked)
            - reasons: list of strings explaining the risk factors found
        """
        risk_score = 0.0
        reasons = []
        now = time.time()

        # 1. Length Exceeded Check
        prompt_len = len(prompt)
        if prompt_len > self.max_length:
            # Score increases proportionally to how much it exceeds the limit
            ratio = prompt_len / self.max_length
            added_risk = min(0.6, 0.3 * ratio)
            risk_score += added_risk
            reasons.append(f"Prompt length ({prompt_len} chars) exceeds limit ({self.max_length} chars)")

        # 2. Anamalous Repetitions Check
        # Clean text and split into words
        words = re.findall(r'\b\w+\b', prompt.lower())
        if len(words) >= 5:
            unique_words = set(words)
            repetition_ratio = 1.0 - (len(unique_words) / len(words))
            
            if repetition_ratio > self.repetition_threshold:
                # Add risk proportional to the severity of repetition
                added_risk = min(0.5, (repetition_ratio - self.repetition_threshold) * 1.5)
                risk_score += added_risk
                reasons.append(f"High token repetition ratio: {repetition_ratio:.2f}")

        # 3. Duplicate Spam Loop Check (Identical prompts in rapid sequence)
        prompt_hash = hashlib.md5(prompt.strip().encode("utf-8")).hexdigest()
        
        # Prune older history (older than 15 seconds) for this client
        if client_id not in self.prompt_history:
            self.prompt_history[client_id] = []
        
        self.prompt_history[client_id] = [
            (t, h) for (t, h) in self.prompt_history[client_id] if now - t < 15.0
        ]
        
        # Count matching hashes in the recent window
        matches = sum(1 for (_, h) in self.prompt_history[client_id] if h == prompt_hash)
        
        # Add to history
        self.prompt_history[client_id].append((now, prompt_hash))

        if matches >= 2:  # Meaning this is at least the 3rd identical prompt in 15 seconds
            risk_score += 0.6
            reasons.append(f"Duplicate prompt detected {matches + 1} times in 15s")

        return risk_score, reasons
