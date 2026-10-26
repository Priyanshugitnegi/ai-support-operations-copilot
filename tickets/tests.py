
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from tickets.ai_service import analyze_ticket
from tickets.schemas import TicketAnalysis


class AnalyzeTicketTests(SimpleTestCase):
    @patch("tickets.ai_service.Groq")
    @patch("tickets.ai_service.search_knowledge_articles")
    def test_analyze_ticket_uses_knowledge_context(
        self,
        mock_search,
        mock_groq,
    ):
        mock_search.return_value = [
            {
                "content": (
                    "Title: Refund Processing Guidelines\n"
                    "Content: Verify refund eligibility."
                ),
                "metadata": {
                    "title": "Refund Processing Guidelines",
                    "source": "Internal Billing Guide",
                },
                "distance": 0.25,
            }
        ]

        expected_result = {
            "summary": "Customer has not received a refund.",
            "category": "billing",
            "priority": "medium",
            "customer_issue": "Refund status is unknown.",
            "recommended_action": (
                "Verify refund eligibility and check the refund status."
            ),
        }

        mock_response = MagicMock()
        mock_response.choices[0].message.content = (
            __import__("json").dumps(expected_result)
        )
        mock_groq.return_value.chat.completions.create.return_value = (
            mock_response
        )

        with patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}):
            result = analyze_ticket(
                "Refund not received",
                "I returned my order but have not received my refund.",
            )

        self.assertIsInstance(result, TicketAnalysis)
        self.assertEqual(result.category, "billing")

        mock_search.assert_called_once()
        mock_groq.return_value.chat.completions.create.assert_called_once()

        call_args = (
            mock_groq.return_value.chat.completions.create.call_args
        )
        user_message = call_args.kwargs["messages"][1]["content"]

        self.assertIn("Refund Processing Guidelines", user_message)
        self.assertIn("Verify refund eligibility", user_message)

    @patch("tickets.ai_service.Groq")
    @patch("tickets.ai_service.search_knowledge_articles")
    def test_analyze_ticket_handles_no_knowledge_articles(
        self,
        mock_search,
        mock_groq,
    ):
        mock_search.return_value = []

        expected_result = {
            "summary": "Customer reports an issue.",
            "category": "general",
            "priority": "low",
            "customer_issue": "The issue needs investigation.",
            "recommended_action": "Ask the customer for more details.",
        }

        mock_response = MagicMock()
        mock_response.choices[0].message.content = (
            __import__("json").dumps(expected_result)
        )
        mock_groq.return_value.chat.completions.create.return_value = (
            mock_response
        )

        with patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}):
            result = analyze_ticket(
                "General question",
                "I need some help.",
            )

        self.assertIsInstance(result, TicketAnalysis)

        call_args = (
            mock_groq.return_value.chat.completions.create.call_args
        )
        user_message = call_args.kwargs["messages"][1]["content"]

        self.assertIn(
            "No relevant knowledge articles were found.",
            user_message,
        )

    @patch("tickets.ai_service.search_knowledge_articles")
    def test_analyze_ticket_requires_api_key(self, mock_search):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(
                RuntimeError,
                "GROQ_API_KEY is missing from .env",
            ):
                analyze_ticket("Test subject", "Test description")

        mock_search.assert_not_called()
