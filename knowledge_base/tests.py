
from unittest.mock import patch

from django.test import TestCase

from knowledge_base.models import KnowledgeArticle
from knowledge_base.services import search_knowledge_articles


class KnowledgeArticleModelTests(TestCase):
    def test_create_knowledge_article(self):
        article = KnowledgeArticle.objects.create(
            title="Refund Processing Guidelines",
            content="Verify refund eligibility before advising the customer.",
            source="Internal Billing Guide",
        )

        self.assertEqual(article.title, "Refund Processing Guidelines")
        self.assertEqual(article.source, "Internal Billing Guide")
        self.assertEqual(
            str(article),
            "Refund Processing Guidelines",
        )


class KnowledgeRetrievalTests(TestCase):
    @patch("knowledge_base.services.collection.query")
    def test_search_returns_retrieved_articles(self, mock_query):
        mock_query.return_value = {
            "documents": [
                [
                    "Title: Refund Processing Guidelines\n"
                    "Content: Verify refund eligibility."
                ]
            ],
            "metadatas": [
                [
                    {
                        "title": "Refund Processing Guidelines",
                        "source": "Internal Billing Guide",
                    }
                ]
            ],
            "distances": [[0.25]],
        }

        results = search_knowledge_articles(
            "Customer has not received a refund."
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["metadata"]["title"],
            "Refund Processing Guidelines",
        )
        self.assertEqual(results[0]["distance"], 0.25)
        mock_query.assert_called_once()

    @patch("knowledge_base.services.collection.query")
    def test_search_returns_empty_list_when_no_articles_found(
        self, mock_query
    ):
        mock_query.return_value = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }

        results = search_knowledge_articles(
            "Question about an unsupported topic."
        )

        self.assertEqual(results, [])
