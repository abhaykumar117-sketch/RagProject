import os
import sys
import warnings
import json

warnings.filterwarnings("ignore")

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
import pymupdf
from rapidocr_onnxruntime import RapidOCR
from langchain_core.documents import Document


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PDF_NAMES = (
    "OOPS UNIT II.ppt.pdf",
    "Introduction_To_Java.pdf",
)


def resolve_pdf_path():
    configured = os.getenv("PDF_PATH")
    if configured:
        candidate = configured if os.path.isabs(configured) else os.path.join(BASE_DIR, configured)
        if os.path.isfile(candidate):
            return candidate

    for filename in DEFAULT_PDF_NAMES:
        candidate = os.path.join(BASE_DIR, filename)
        if os.path.isfile(candidate):
            return candidate

    pdf_files = [
        os.path.join(BASE_DIR, filename)
        for filename in os.listdir(BASE_DIR)
        if filename.lower().endswith(".pdf")
    ]
    if pdf_files:
        return sorted(pdf_files)[0]
    return os.path.join(BASE_DIR, "Introduction_To_Java.pdf")


PDF_PATH = resolve_pdf_path()
COLLECTION_NAME = "pdf_knowledge"
OCR_CACHE_PATH = os.path.join(BASE_DIR, "pdf_ocr_cache.json")

JAVA_TOPIC_WORDS = {
    "java", "jdk", "jre", "jvm", "javac", "bytecode", "class", "object",
    "oop", "inheritance", "polymorphism", "encapsulation", "abstraction",
    "interface", "abstract", "constructor", "method", "function",
    "package", "access", "public", "private", "protected", "static",
    "final", "enum", "record", "sealed", "generics", "generic",
    "collection", "collections", "list", "array", "arraylist", "linkedlist",
    "hashmap", "map", "set", "queue", "deque", "stream", "streams",
    "lambda", "exception", "try", "catch", "throw", "throws", "finally",
    "thread", "threads", "concurrency", "synchronization", "synchronized",
    "multithreading", "runnable", "executor", "junit", "maven", "gradle",
    "spring", "springboot", "hibernate", "jdbc", "servlet", "jsp",
    "input", "output", "scanner", "iostream", "string", "integer",
    "boolean", "loop", "for", "while", "switch", "if", "else",
    "operator", "variable", "datatype", "data type", "compiler",
}


def extract_pdf_documents():
    pdf = pymupdf.open(PDF_PATH)
    ocr = RapidOCR()
    documents = []
    cached_pages = []
    cache_identity = {
        "filename": os.path.basename(PDF_PATH),
        "size": os.path.getsize(PDF_PATH),
    }

    if os.path.isfile(OCR_CACHE_PATH):
        try:
            with open(OCR_CACHE_PATH, "r", encoding="utf-8") as cache_file:
                cache_data = json.load(cache_file)
        except json.JSONDecodeError:
            cache_data = {}
        if isinstance(cache_data, dict) and cache_data.get("identity") == cache_identity:
            cached_pages = cache_data.get("pages", [])
            print(f"Loaded OCR text cache with {len(cached_pages)} pages.")

    print("Extracting and OCR-reading PDF pages. This may take several minutes...")
    print("Progress is saved every 25 pages, so restarting will resume cached work.")
    cached_by_page = {
        item["page"]: item["text"]
        for item in cached_pages
        if item.get("text", "").strip()
    }
    for page_index in range(len(pdf)):
        if page_index in cached_by_page:
            continue

        page = pdf[page_index]
        text = page.get_text("text").strip()
        if len(text) < 100:
            pixmap = page.get_pixmap(matrix=pymupdf.Matrix(1.0, 1.0), alpha=False)
            image = pixmap.tobytes("png")
            import cv2
            import numpy as np
            decoded = cv2.imdecode(np.frombuffer(image, dtype=np.uint8), cv2.IMREAD_COLOR)
            if decoded is not None:
                ocr_result, _ = ocr(decoded)
                if ocr_result:
                    text = "\n".join(
                        line[1].strip()
                        for line in ocr_result
                        if len(line) >= 2 and line[1].strip()
                    )

        if text.strip():
            documents.append(Document(
                page_content=text,
                metadata={"page": page_index},
            ))
            cached_pages.append({"page": page_index, "text": text})

        if (page_index + 1) % 25 == 0:
            print(f"Processed {page_index + 1}/{len(pdf)} pages")
            with open(OCR_CACHE_PATH, "w", encoding="utf-8") as cache_file:
                json.dump(
                    {"identity": cache_identity, "pages": cached_pages},
                    cache_file,
                    ensure_ascii=False,
                )

    with open(OCR_CACHE_PATH, "w", encoding="utf-8") as cache_file:
        json.dump(
            {"identity": cache_identity, "pages": cached_pages},
            cache_file,
            ensure_ascii=False,
        )

    if cached_by_page:
        cached_by_page.update(
            {
                item["page"]: item["text"]
                for item in cached_pages
                if item.get("text", "").strip()
            }
        )
        documents = [
            Document(
                page_content=text,
                metadata={"page": page_index},
            )
            for page_index, text in sorted(cached_by_page.items())
        ]

    return documents


def build_rag_chain():
    load_dotenv(os.path.join(BASE_DIR, ".env"))
    global PDF_PATH, OCR_CACHE_PATH
    PDF_PATH = resolve_pdf_path()
    OCR_CACHE_PATH = os.path.join(
        BASE_DIR,
        f"pdf_ocr_cache_{os.path.splitext(os.path.basename(PDF_PATH))[0]}.json",
    )
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "replace-with-your-new-groq-api-key":
        raise RuntimeError(
            "GROQ_API_KEY is missing. Create a new key in Groq Console, "
            "then set it in the .env file."
        )
    if not os.path.isfile(PDF_PATH):
        raise FileNotFoundError(f"PDF not found: {PDF_PATH}")

    print(f"Loading PDF: {PDF_PATH}")
    docs = extract_pdf_documents()
    if not docs:
        raise RuntimeError("The PDF could not be read.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    print(f"Loaded {len(docs)} pages and created {len(chunks)} chunks.")

    embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    client = QdrantClient(location=":memory:")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )
    vectorstore = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=embeddings,
    )
    vectorstore.add_documents(chunks)

    llm = ChatGroq(
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        groq_api_key=api_key,
        temperature=0.2,
        max_tokens=2500,
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a patient study assistant for the user's PDF. Base claims "
                "about the document only on the supplied PDF context; do not pretend "
                "that retrieved excerpts cover parts of the PDF that are not shown. "
                "Answer in the same language and style as the question: use simple "
                "Hindi for Hindi questions and natural Hinglish for Hinglish questions. "
                "Explain relevant concepts clearly, and add a short example when it "
                "helps the student understand. For summaries, definitions, revision "
                "notes, or exam questions, use the supplied PDF context and do not "
                "invent document content. If a question is related to the PDF topic "
                "but its answer is not present in the context, say so plainly, then "
                "give a clearly labeled general-knowledge explanation if you can. "
                "If the question is unrelated to the PDF topic, politely say that "
                "you are focused on this PDF. Distinguish PDF-based facts from "
                "general explanations, and cite only page numbers present in the "
                "context; omit page citations if none are available. "
                "Do not invent facts or page numbers.\n\n"
                "PDF context:\n{context}",
            ),
            ("human", "{question}"),
        ]
    )
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5},
    )
    chain = prompt | llm | StrOutputParser()
    return retriever, chain, vectorstore


def query_rag(question, retriever, chain, vectorstore):
    retrieved_with_scores = vectorstore.similarity_search_with_score(question, k=5)
    if not retrieved_with_scores:
        return chain.invoke({
            "context": "No relevant PDF context was found.",
            "question": question,
        })

    best_score = max(score for _, score in retrieved_with_scores)
    retrieved_docs = [doc for doc, _ in retrieved_with_scores]
    context_parts = []
    for doc in retrieved_docs:
        page = doc.metadata.get("page")
        page_number = page + 1 if isinstance(page, int) else "?"
        context_parts.append(f"[Page {page_number}]\n{doc.page_content}")

    context = "\n\n".join(context_parts)
    answer = chain.invoke({"context": context, "question": question})
    if "I could not find this information in the PDF." in answer:
        return "I could not find this information in the PDF."
    return answer


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    try:
        retriever, chain, vectorstore = build_rag_chain()
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"\nPDF AI Assistant is ready. Loaded: {os.path.basename(PDF_PATH)}")
    print("Ask questions, or type 'exit' to quit.")
    while True:
        try:
            question = input("\nQuestion: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if question.lower() in {"exit", "quit", "q"}:
            break
        if not question:
            continue

        print("\nAnswer:")
        try:
            print(query_rag(question, retriever, chain, vectorstore))
        except Exception as exc:
            message = str(exc)
            if "model_not_found" in message or "does not exist" in message:
                print(
                    "The configured Groq model is unavailable. "
                    "Set GROQ_MODEL in .env to a model available in your Groq account."
                )
            elif "invalid_api_key" in message or "401" in message:
                print("Groq API key is invalid or expired. Add a new key to .env.")
            else:
                print(f"Could not answer the question: {message}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
