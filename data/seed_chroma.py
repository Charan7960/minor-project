import os
import math
import shutil
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_store")

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


POLICY_DOCUMENTS = [
    {"id": "POL001", "topic": "Return window",
     "text": "Customers may return any product within 7 days of delivery for a full refund. The 7-day window starts from the delivered_at date. Returns after 7 days are not eligible unless the item is defective."},
    {"id": "POL002", "topic": "Damaged or defective items",
     "text": "If a customer receives a damaged or defective item, they are eligible for a full refund or free replacement regardless of when they report it, provided they submit a complaint within 30 days of delivery. Photo evidence must be emailed to support@shopvoice.in."},
    {"id": "POL003", "topic": "Wrong item delivered",
     "text": "If a customer receives an item different from what was ordered, they are entitled to a free return pickup and full refund or reshipment. No time limit applies. The agent should immediately approve a refund or replacement without escalation."},
    {"id": "POL004", "topic": "Refund approval threshold",
     "text": "Refunds up to Rs. 5000 can be approved autonomously by the voice agent. Refunds above Rs. 5000 require manager approval and must be escalated to a human agent. The customer should be informed their case will be reviewed within 24 hours."},
    {"id": "POL005", "topic": "Refund processing time",
     "text": "Once a refund is approved, the amount is credited back within 5-7 business days. UPI and wallet payments are refunded within 24 hours. Customers can track refund status by asking the agent or visiting the app."},
    {"id": "POL006", "topic": "Order cancellation",
     "text": "Orders can be cancelled for free before they are shipped. Once an order is shipped or delivered, it cannot be cancelled, only returned. The agent can cancel processing orders immediately. Refunds for cancellations are processed within 3 business days."},
    {"id": "POL007", "topic": "Membership benefits",
     "text": "Gold members receive priority support, free returns on all orders, and a dedicated callback within 2 hours. Silver members receive free returns on orders above Rs. 1000 and callbacks within 4 hours. Standard members follow the default 7-day return window with no priority."},
    {"id": "POL008", "topic": "Escalation to human agent",
     "text": "The voice agent must escalate to a human agent when: refund amount exceeds Rs. 5000, customer expresses extreme dissatisfaction three or more times, legal or fraud complaints are raised, or the agent cannot resolve the issue after two attempts."},
    {"id": "POL009", "topic": "Exchange policy",
     "text": "Exchanges are allowed within 7 days of delivery for size or colour variants of the same product, subject to stock availability. If the desired variant is out of stock, offer a full refund instead."},
    {"id": "POL010", "topic": "Non-returnable items",
     "text": "The following categories are non-returnable unless defective: personal care products, innerwear, food and consumables, and software licenses. If a customer requests a return on these items and they are not defective, politely decline and offer a discount coupon as a goodwill gesture."},
]


def build_vector_store():
    print(f"[ChromaDB] Initialising store at: {CHROMA_PATH}\n")
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)
        print("[ChromaDB] Cleared existing store.")

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    ef = LocalTFIDFEmbedding(dim=256)

    collection = client.create_collection(
        name="policy_handbook",
        metadata={"description": "ShopVoice policy handbook"},
    )

    ids        = [d["id"]   for d in POLICY_DOCUMENTS]
    documents  = [d["text"] for d in POLICY_DOCUMENTS]
    metadatas  = [{"topic": d["topic"]} for d in POLICY_DOCUMENTS]
    embeddings = ef(documents)

    collection.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
    print(f"[ChromaDB] Embedded {len(POLICY_DOCUMENTS)} policy chunks.\n")
    return collection, ef


def verify(collection, ef):
    print("[ChromaDB] Verification — sample retrieval:")
    test_queries = [
        "Can I return a damaged item?",
        "How long does a refund take?",
        "What happens if I got the wrong product?",
    ]
    for q in test_queries:
        q_embedding = ef([q])
        results = collection.query(query_embeddings=q_embedding, n_results=1)
        top_topic = results["metadatas"][0][0]["topic"]
        top_text  = results["documents"][0][0][:80]
        print(f"\n  Query : {q}")
        print(f"  Match : [{top_topic}] {top_text}...")


if __name__ == "__main__":
    collection, ef = build_vector_store()
    verify(collection, ef)
    print("\n[ChromaDB] Phase 1b complete. Policy vector store ready.")
