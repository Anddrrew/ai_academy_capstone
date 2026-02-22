import time

from qdrant_client.models import PointStruct

from shared.services.base_storage import BaseStorage


class EvaluationStorage(BaseStorage):
    collection_name = "evaluation_log"

    def save(
        self,
        user_input: str,
        agent_output: str,
        tool_calls: list[str],
        score: str,
        feedback: str,
        vector: list[float],
    ) -> None:
        point_id = int(time.time() * 1000)
        self._client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "user_input": user_input,
                        "agent_output": agent_output,
                        "tool_calls": tool_calls,
                        "score": score,
                        "feedback": feedback,
                        "created_at": int(time.time()),
                    },
                )
            ],
        )
        self.logger.info("Logged evaluation: score=%s, id=%d", score, point_id)


evaluation_storage = EvaluationStorage()
