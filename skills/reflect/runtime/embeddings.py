"""The selected local Gemma profile, loaded only for explicit derived work."""
import hashlib
import json
from pathlib import Path

from records import RecordError, digest, encoded

PROFILE = json.loads((Path(__file__).parent / "embedding_profile.json").read_text())
PROFILE_SHA = digest(encoded(PROFILE))


class Gemma:
    def __init__(self, model_path):
        root = Path(model_path).resolve()
        for artifact in PROFILE["artifacts"]:
            path = root / artifact["path"]
            try:
                with path.open("rb") as stream:
                    actual = hashlib.file_digest(stream, "sha256").hexdigest()
            except OSError:
                raise RecordError("embedding-model-unavailable") from None
            if actual != artifact["sha256"]:
                raise RecordError("embedding-model-mismatch")
        try:
            import torch
            from sentence_transformers import SentenceTransformer
            torch.set_num_threads(4)
            self.model = SentenceTransformer(str(root), device="cpu", model_kwargs={"dtype": torch.float32}, local_files_only=True, trust_remote_code=False, token=False)
            self.model.max_seq_length = PROFILE["max_tokens"]
            if self.model.get_embedding_dimension() != PROFILE["dimensions"]:
                raise RecordError("embedding-model-mismatch")
        except (ImportError, OSError, ValueError):
            raise RecordError("embedding-model-unavailable") from None

    def encode(self, text, role):
        if role not in ("query", "document") or not isinstance(text, str) or not text.strip():
            raise RecordError("invalid-embedding-input")
        prompt = PROFILE[role + "_prompt"]
        count = len(self.model.tokenizer.encode(prompt + text, truncation=False))
        vector = self.model.encode([text], prompt=prompt, batch_size=1, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)[0]
        return vector.tolist(), {"kind": "gemma", "version": PROFILE["revision"], "token_count": count, "truncated": count > PROFILE["max_tokens"]}
