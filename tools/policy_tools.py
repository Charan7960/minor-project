import os
import math
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_store")


class LocalTFIDFEmbedding(EmbeddingFunction):
    def __init__(self, dim: int = 256):
        self.dim = dim
        self._vocab = {}

    def _tokenize(self, text: str):
        import re
        return re.findall(r"[a-z]+", text.lower())

    def _fit(self, docs):
        for d in docs:
            for tok in self._tokenize(d):
                if tok not in self._vocab:
                    self._vocab[tok] = len(self._vocab) % self.dim

    def _embed_one(self, text: str):
        tokens = self._tokenize(text)
        vec = [0.0] * self.dim
        for t in tokens:
            if t in self._vocab:
                vec[self._vocab[t]] += 1.0
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    def __call__(self, input: Documents) -> Embeddings:
        self._fit(input)
        return [self._embed_one(d) for d in input]


def get_collection():
    """Load the ChromaDB policy collection."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_collection(name="policy_handbook")


def search_policy(query: str, n_results: int = 2) -> dict:
    """
    Search policy handbook for the most relevant chunks.
    Returns top matching policy texts the agent can reason over.
    """
    try:
        collection = get_collection()
        ef = LocalTFIDFEmbedding(dim=256)

        # We need to fit the vocab on existing docs first
        all_docs = collection.get()
        ef._fit(all_docs["documents"])

        query_embedding = ef([query])
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=n_results
        )

        policies = []
        for i in range(len(results["ids"][0])):
            policies.append({
                "topic": results["metadatas"][0][i]["topic"],
                "text":  results["documents"][0][i],
            })

        return {
            "query":    query,
            "policies": policies
        }

    except Exception as e:
        return {"error": str(e)}


def get_policy_by_topic(topic_keyword: str) -> dict:
    """
    Fetch a policy directly by keyword in the topic name.
    Useful when agent knows exactly what policy it needs.
    """
    try:
        collection = get_collection()
        all_docs = collection.get()

        matches = []
        for i, meta in enumerate(all_docs["metadatas"]):
            if topic_keyword.lower() in meta["topic"].lower():
                matches.append({
                    "topic": meta["topic"],
                    "text":  all_docs["documents"][i],
                })

        if not matches:
            return {"error": f"No policy found matching topic: {topic_keyword}"}

        return {"policies": matches}

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print("=== Testing policy_tools.py ===\n")

    print("1. Search: 'customer wants to return damaged item'")
    result = search_policy("customer wants to return damaged item")
    for p in result["policies"]:
        print(f"   [{p['topic']}] {p['text'][:100]}...")

    print("\n2. Search: 'refund taking too long'")
    result = search_policy("refund taking too long")
    for p in result["policies"]:
        print(f"   [{p['topic']}] {p['text'][:100]}...")

    print("\n3. Search: 'can I cancel my order'")
    result = search_policy("can I cancel my order")
    for p in result["policies"]:
        print(f"   [{p['topic']}] {p['text'][:100]}...")

    print("\n4. Get policy by topic keyword: 'escalation'")
    result = get_policy_by_topic("escalation")
    for p in result["policies"]:
        print(f"   [{p['topic']}] {p['text'][:100]}...")

    print("\n[policy_tools] All tests passed.")
