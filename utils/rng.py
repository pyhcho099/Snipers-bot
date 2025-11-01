import hashlib
import time
from config import config

class ProvablyFairRNG:
    def __init__(self):
        self.server_seed = config.CASINO_SERVER_SEED
    
    def generate(self, client_seed: str) -> float:
        """Generate a provably fair random number between 0 and 1"""
        nonce = str(int(time.time() * 1000000))
        combined = f"{self.server_seed}{client_seed}{nonce}"
        hash_result = hashlib.sha256(combined.encode()).hexdigest()
        return int(hash_result[:8], 16) / 0xffffffff
    
    def verify(self, client_seed: str, nonce: str, result: float) -> bool:
        """Verify the fairness of a result"""
        combined = f"{self.server_seed}{client_seed}{nonce}"
        hash_result = hashlib.sha256(combined.encode()).hexdigest()
        expected = int(hash_result[:8], 16) / 0xffffffff
        return abs(result - expected) < 0.0001

rng = ProvablyFairRNG()
