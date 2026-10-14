import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, List
import redis

logger = logging.getLogger("api_gateway.rate_limiter")

class RateLimiterBackend(ABC):
    @abstractmethod
    def is_allowed(self, client_id: str, limit: int, window_seconds: int) -> bool:
        """
        Check if the client_id has exceeded the request limit within the sliding window.
        Returns True if request is allowed, False otherwise.
        """
        pass


class InMemoryRateLimiter(RateLimiterBackend):
    def __init__(self):
        # Maps client_id to list of timestamps of successful requests
        self.history: Dict[str, List[float]] = {}

    def is_allowed(self, client_id: str, limit: int, window_seconds: int) -> bool:
        now = time.time()
        boundary = now - window_seconds
        
        if client_id not in self.history:
            self.history[client_id] = [now]
            return True
            
        # Prune expired timestamps
        self.history[client_id] = [t for t in self.history[client_id] if t > boundary]
        
        if len(self.history[client_id]) < limit:
            self.history[client_id].append(now)
            return True
            
        return False


class RedisRateLimiter(RateLimiterBackend):
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        try:
            self.client = redis.Redis.from_url(redis_url, decode_responses=True)
            self.client.ping()
            logger.info("Successfully connected to Redis for rate limiting.")
            self.active = True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}. Falling back to InMemory rate limiter.")
            self.active = False
            self.fallback_limiter = InMemoryRateLimiter()

    def is_allowed(self, client_id: str, limit: int, window_seconds: int) -> bool:
        if not self.active:
            return self.fallback_limiter.is_allowed(client_id, limit, window_seconds)
            
        now = time.time()
        clear_before = now - window_seconds
        key = f"rate_limit:{client_id}"
        
        try:
            lua_script = """
            redis.call('ZREMRANGEBYSCORE', KEYS[1], 0, ARGV[1])
            local current_count = redis.call('ZCARD', KEYS[1])
            if current_count >= tonumber(ARGV[2]) then
                return 0
            else
                redis.call('ZADD', KEYS[1], ARGV[3], ARGV[4])
                redis.call('EXPIRE', KEYS[1], ARGV[5])
                return 1
            end
            """
            member = f"{now}:{time.time_ns()}"
            result = self.client.eval(lua_script, 1, key, clear_before, limit, now, member, window_seconds)
            return result == 1
            
        except redis.RedisError as e:
            logger.error(f"Redis operation error: {e}. Defaulting to InMemory limiter.")
            # Create a fallback inline or activate fallback
            self.active = False
            self.fallback_limiter = InMemoryRateLimiter()
            return self.fallback_limiter.is_allowed(client_id, limit, window_seconds)


# Policy Definitions
ROLE_POLICIES = {
    # Note: "admin" role is explicitly bypassed in main.py and does not use these policies
    "employee": {"limit": 60, "window": 60},   # 60 req/minute
    "guest": {"limit": 5, "window": 60}        # 5 req/minute
}

def get_rate_limiter_policy(role: str) -> dict:
    return ROLE_POLICIES.get(role, ROLE_POLICIES["guest"])
