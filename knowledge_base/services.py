
import chromadb

from knowledge_base.models import KnowledgeArticle


client = chromadb.PersistentClient(path="./vector_store")

collection = client.get_or_create_collection(
    name="support_knowledge"
)


def ingest_knowledge_articles():
    articles = KnowledgeArticle.objects.all()

    for article in articles:
        collection.upsert(
            ids=[str(article.id)],
            documents=[
                f"Title: {article.title}\n"
                f"Source: {article.source}\n"
                f"Content: {article.content}"
            ],
            metadatas=[
                {
                    "title": article.title,
                    "source": article.source,
                }
            ],
        )

    return articles.count()



def search_knowledge_articles(query, n_results=2):
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
    )

    articles = []

    for i, document in enumerate(results["documents"][0]):
        articles.append(
            {
                "content": document,
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            }
        )

    return articles
