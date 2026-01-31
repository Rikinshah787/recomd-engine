# Uber Shopping: Architectural Case Study (Ranking & Discovery MVP)

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![HuggingFace](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Models-orange)](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
[![FAISS](https://img.shields.io/badge/Vector--DB-FAISS-green?style=for-the-badge)](https://github.com/facebookresearch/faiss)

## 🎯 Executive Summary
This project is a technical implementation of a high-performance **Product Ranking and Recommendation Engine**, engineered as a direct response to the architectural requirements outlined in **Uber's Shopping Ranking** engineering specifications. 

Rather than basic keyword matching, this system implements a **Production-Grade 4-Stage Pipeline** to handle high-concurrency semantic discovery and transparent ranking.

---

## 🛠️ Built to Uber Engineering Specs

| Requirement | Implementation | Technical Detail |
| :--- | :--- | :--- |
| **Semantic Intelligence** | **Vector Embeddings** | Leveraged `all-MiniLM-L6-v2` via Sentence-Transformers (Hugging Face). |
| **Candidate Retrieval**| **FAISS L1 Indexing** | Facebook AI Similarity Search for sub-millisecond neighbor retrieval. |
| **Signal Fusion** | **Weighted Arithmetic Scorer** | Real-time blending of Price, Popularity, Rating, and Category signals. |
| **Explainability** | **Generative NL Layer** | Dynamic natural-language explanations for ranking transparency. |
| **Scalability** | **Dockerized Microservice** | Containerized FastAPI backend with asynchronous request handling. |

---

## 📐 System Architecture

The Discovery Engine follows a strict **4-Stage Pipeline** pattern used in global-scale e-commerce:

1.  **Stage 1: Retrieval (L1)**: Performs high-dimensional vector math inside a FAISS index to extract the top 100 most relevant candidates from the catalog.
2.  **Stage 2: Enrichment**: Injects real-time business signals (Price score, Market Demand, Trust Index) into the candidate pool.
3.  **Stage 3: Scoring (L2)**: Applies a tuned weighted model to determine the final rank based on the fusion of semantic match + business signals.
4.  **Stage 4: Explainability**: Generates contextual "highlights" and human-readable reasoning for each ranking position.

---

## 🚀 Experience it Live

*   **Frontend**: [Uber UI (Vercel)](https://recomd-engine.vercel.app)
*   **Backend**: [AI Engine API (Railway)](https://recomd-engine-production.up.railway.app)
*   **Interactive Docs**: [Swagger API Documentation](https://recomd-engine-production.up.railway.app/docs)

---

## 💻 Technical Stack

### **Backend (The Engine)**
- **Framework**: Python FastAPI (Async/Await)
- **Vector Index**: FAISS (Facebook AI Similarity Search)
- **Embeddings**: Hugging Face `all-MiniLM-L6-v2`
- **Logic**: Multi-signal ranking algorithm

### **Frontend (The Experience)**
- **Framework**: React.js with Vite
- **Styling**: Uber-inspired High-Contrast Dark Theme
- **UX**: Real-time search with latency benchmarking and semantic highlighting

---

## 📥 Local Setup & Development

```bash
# 1. Clone & Install
git clone https://github.com/Rikinshah787/recomd-engine.git
pip install -r requirements.txt

# 2. Re-Index Database (2,000 Products)
python scripts/generate_data.py
python scripts/build_embeddings.py

# 3. Launch
uvicorn app.main:app --reload
```

---

## 📄 Final Thoughts
This MVP demonstrates a complete journey from **Job Description Analysis** to **Production Deployment**. It solves the core Information Retrieval (IR) challenges of discovery: balancing semantic relevancy with business objectives.

**Contact**: [rshah88@asu.edu](mailto:rshah88@asu.edu)
