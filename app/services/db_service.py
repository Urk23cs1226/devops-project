"""Database service — async MongoDB operations using motor."""

from datetime import datetime, timedelta
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings


class DatabaseService:
    """Manages MongoDB connection and prediction CRUD operations."""

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self._connected = False

    async def connect(self):
        """Establish connection to MongoDB."""
        settings = get_settings()
        try:
            self.client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=5000
            )
            # Test connection
            await self.client.admin.command("ping")
            self.db = self.client[settings.DATABASE_NAME]
            self._connected = True
            print(f"[OK] Connected to MongoDB: {settings.DATABASE_NAME}")
        except Exception as e:
            print(f"[WARN] MongoDB connection failed: {e}")
            print("   Predictions will NOT be saved to database.")
            self._connected = False

    async def disconnect(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self._connected = False
            print("[--] MongoDB disconnected")

    async def save_prediction(self, prediction_data: dict) -> Optional[str]:
        """Save a prediction record to the database."""
        if not self._connected:
            return None

        record = {
            "disease": prediction_data["disease"],
            "confidence": prediction_data["confidence"],
            "symptoms": prediction_data["symptoms_used"],
            "symptoms_matched": prediction_data["symptoms_matched"],
            "top_predictions": prediction_data["top_predictions"],
            "timestamp": datetime.utcnow(),
        }

        result = await self.db.predictions.insert_one(record)
        return str(result.inserted_id)

    async def get_history(
        self, page: int = 1, limit: int = 20, search: str = ""
    ) -> dict:
        """Get paginated prediction history."""
        if not self._connected:
            return {"predictions": [], "total": 0, "page": page,
                    "limit": limit, "total_pages": 0}

        query = {}
        if search:
            query["disease"] = {"$regex": search, "$options": "i"}

        total = await self.db.predictions.count_documents(query)
        skip = (page - 1) * limit

        cursor = self.db.predictions.find(query).sort(
            "timestamp", -1
        ).skip(skip).limit(limit)

        predictions = []
        async for doc in cursor:
            predictions.append({
                "id": str(doc["_id"]),
                "disease": doc["disease"],
                "confidence": doc["confidence"],
                "symptoms": doc.get("symptoms", []),
                "top_predictions": doc.get("top_predictions", []),
                "timestamp": doc["timestamp"].isoformat(),
            })

        total_pages = max(1, (total + limit - 1) // limit)

        return {
            "predictions": predictions,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
        }

    async def get_stats(self) -> dict:
        """Get aggregate statistics about predictions."""
        if not self._connected:
            return {
                "total_predictions": 0,
                "top_diseases": [],
                "avg_confidence": 0,
                "recent_predictions": 0,
            }

        total = await self.db.predictions.count_documents({})

        # Top diseases pipeline
        top_diseases_pipeline = [
            {"$group": {"_id": "$disease", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10},
        ]
        top_diseases = []
        async for doc in self.db.predictions.aggregate(top_diseases_pipeline):
            top_diseases.append({"disease": doc["_id"], "count": doc["count"]})

        # Average confidence
        avg_pipeline = [
            {"$group": {"_id": None, "avg_confidence": {"$avg": "$confidence"}}}
        ]
        avg_confidence = 0
        async for doc in self.db.predictions.aggregate(avg_pipeline):
            avg_confidence = round(doc["avg_confidence"], 2)

        # Recent predictions (last 24 hours)
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent = await self.db.predictions.count_documents(
            {"timestamp": {"$gte": recent_cutoff}}
        )

        return {
            "total_predictions": total,
            "top_diseases": top_diseases,
            "avg_confidence": avg_confidence,
            "recent_predictions": recent,
        }


# Singleton instance
db_service = DatabaseService()
