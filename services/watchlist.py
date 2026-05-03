import json
import os
import threading
from typing import List, Dict

WATCHLIST_FILE = "watchlist.json"

class WatchlistService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(WatchlistService, cls).__new__(cls)
                cls._instance._init_once()
            return cls._instance

    def _init_once(self):
        self._data = self._load()
        self._file_lock = threading.Lock()
        
    def _load(self) -> dict:
        if not os.path.exists(WATCHLIST_FILE):
            return {}
        try:
            with open(WATCHLIST_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
            
    def _save(self):
        with self._file_lock:
            with open(WATCHLIST_FILE, 'w') as f:
                json.dump(self._data, f, indent=4)
            
    def add(self, user_id: int, channel_id: int, symbol: str) -> bool:
        uid = str(user_id)
        if uid not in self._data:
            self._data[uid] = {"channel_id": str(channel_id), "symbols": []}
            
        self._data[uid]["channel_id"] = str(channel_id)
        
        symbol = symbol.upper()
        if symbol not in self._data[uid]["symbols"]:
            self._data[uid]["symbols"].append(symbol)
            self._save()
            return True
        return False
        
    def remove(self, user_id: int, symbol: str) -> bool:
        uid = str(user_id)
        if uid in self._data:
            symbol = symbol.upper()
            if symbol in self._data[uid]["symbols"]:
                self._data[uid]["symbols"].remove(symbol)
                self._save()
                return True
        return False
        
    def get_user_symbols(self, user_id: int) -> List[str]:
        uid = str(user_id)
        return self._data.get(uid, {}).get("symbols", [])
        
    def get_all_targets(self) -> Dict[str, List[Dict]]:
        targets = {}
        for uid, info in self._data.items():
            for sym in info.get("symbols", []):
                if sym not in targets:
                    targets[sym] = []
                targets[sym].append({"user_id": uid, "channel_id": info.get("channel_id")})
        return targets
