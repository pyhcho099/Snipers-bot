from models.enums import TransactionType

class TransactionService:
    def __init__(self, db):
        self.db = db
    
    async def create_transaction(self, user_id: int, txn_type: TransactionType, 
                                 amount: int, balance_after: int, reason: str, 
                                 metadata: dict = None):
        """Create a transaction record"""
        import json
        metadata_json = json.dumps(metadata) if metadata else '{}'
        
        await self.db.execute("""
            INSERT INTO transactions (user_id, type, amount, balance_after, reason, metadata)
            VALUES ($1, $2::txn_type, $3, $4, $5, $6::jsonb)
        """, user_id, txn_type.value, amount, balance_after, reason, metadata_json)
    
    async def get_user_transactions(self, user_id: int, limit: int = 10):
        """Get user transaction history"""
        return await self.db.fetch("""
            SELECT * FROM transactions 
            WHERE user_id = $1 
            ORDER BY created_at DESC 
            LIMIT $2
        """, user_id, limit)
