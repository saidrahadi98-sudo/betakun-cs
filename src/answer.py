"""ask(question) -> answer, sources, handoff. Used by app.py and the evaluation scripts."""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DB_DIR = BASE / "db"
EMBED_MODEL = "intfloat/multilingual-e5-base"
TOP_K = 4
CUTOFF = 0.45  # best distance above this means "not sure"; tune it with the evaluation
SOURCES_SHOWN = 2
MARKER = "[HANDOFF]"  # the model answers with this when the FAQ cannot answer the question

HANDOFF_MESSAGE = (
    "Maaf, saya belum yakin dengan jawabannya. Saya hubungkan Anda ke agen manusia kami ya. "
    "Layanan pelanggan BorneoNet buka setiap hari pukul 08.00 hingga 21.00 WITA, "
    "WhatsApp 0811-0000-0000."
)

SYSTEM = """Jika jawabannya tidak ada di FAQ, atau pertanyaan tidak berhubungan dengan layanan BorneoNet, 
balas HANYA dengan kata [HANDOFF] tanpa tambahan apa pun.

Aturan:
- Jika pelanggan memakai bahasa santai atau singkatan, jawab dengan Indonesia yang sopan dan mudah dimengerti.
- Jika pelanggan memakai bahasa Banjar, pahami maksudnya dan jawab dalam bahasa Indonesia yang mudah dimengerti.
- Pakai angka, harga, dan aturan persis seperti di FAQ. Jangan menambah informasi sendiri.
- Jika jawabannya tidak ada di FAQ, katakan kamu tidak yakin dan tawarkan untuk menghubungkan ke agen manusia.
- Jawab singkat, maksimal 4 kalimat. Jangan menyebut kata 'FAQ' atau 'konteks'."""

_state = {}


def _load():
    """Load the embedding model and the database once, on first use."""
    if not _state:
        import chromadb
        from sentence_transformers import SentenceTransformer

        _state["model"] = SentenceTransformer(EMBED_MODEL)
        _state["col"] = chromadb.PersistentClient(path=str(DB_DIR)).get_collection("faq")
    return _state["model"], _state["col"]


def retrieve(question, k=TOP_K):
    """Return the k closest FAQ entries as dicts with source, text and distance."""
    model, col = _load()
    emb = model.encode(["query: " + question], normalize_embeddings=True).tolist()
    res = col.query(query_embeddings=emb, n_results=k)
    return [
        {"source": meta["source"], "text": doc, "distance": dist}
        for meta, doc, dist in zip(res["metadatas"][0], res["documents"][0], res["distances"][0])
    ]


def build_user_message(question, chunks):
    context = "\n\n---\n\n".join(c["text"] for c in chunks)
    return f"FAQ:\n{context}\n\nPertanyaan pelanggan: {question}"


def ask(question, retrieve_fn=None, generate_fn=None):
    """Answer one customer question. The two *_fn arguments exist so tests can fake them."""
    retrieve_fn = retrieve_fn or retrieve
    chunks = retrieve_fn(question)
    best = chunks[0]["distance"] if chunks else 9.9

    if not chunks or best > CUTOFF:
        return {"answer": HANDOFF_MESSAGE, "sources": [], "handoff": True, "best_distance": best}

    if generate_fn is None:
        from src.llm import generate as generate_fn
    answer = generate_fn(SYSTEM, build_user_message(question, chunks))
    if MARKER in answer:
        return {"answer": HANDOFF_MESSAGE, "sources": [], "handoff": True, "best_distance": best}
    sources = [c["source"] for c in chunks[:SOURCES_SHOWN]]
    return {"answer": answer, "sources": sources, "handoff": False, "best_distance": best}
