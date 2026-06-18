from langchain.schema import Document

from src.chat_memory import append_turn, format_history_for_input
from src.helper import filter_to_minimal_docs, text_split


class TestChatMemory:
    def test_format_history_for_input_without_history(self):
        assert format_history_for_input([], "hello") == "hello"

    def test_format_history_for_input_with_history(self):
        history = [{"user": "Hi", "assistant": "Hello"}]
        formatted = format_history_for_input(history, "Follow up")

        assert "User: Hi" in formatted
        assert "Assistant: Hello" in formatted
        assert "User: Follow up" in formatted

    def test_append_turn(self):
        history = append_turn(None, "question", "answer")

        assert history == [{"user": "question", "assistant": "answer"}]

        updated = append_turn(history, "next", "reply")
        assert len(updated) == 2
        assert updated[1]["user"] == "next"


class TestHelperFunctions:
    def test_filter_to_minimal_docs(self):
        docs = [
            Document(page_content="alpha", metadata={"source": "a.pdf", "page": 1}),
            Document(page_content="beta", metadata={"source": "b.pdf", "extra": "x"}),
        ]

        filtered = filter_to_minimal_docs(docs)

        assert len(filtered) == 2
        assert filtered[0].page_content == "alpha"
        assert filtered[0].metadata == {"source": "a.pdf"}
        assert filtered[1].metadata == {"source": "b.pdf"}

    def test_text_split_creates_multiple_chunks(self):
        long_text = "word " * 300
        docs = [Document(page_content=long_text, metadata={"source": "doc.pdf"})]

        chunks = text_split(docs)

        assert len(chunks) > 1
        assert all(chunk.metadata["source"] == "doc.pdf" for chunk in chunks)
        assert sum(len(chunk.page_content) for chunk in chunks) >= len(long_text) - 100

    def test_load_pdf_file_uses_directory_loader(self, mocker):
        from src.helper import load_pdf_file

        mock_loader = mocker.patch("src.helper.DirectoryLoader")
        expected_docs = [Document(page_content="pdf text", metadata={"source": "file.pdf"})]
        mock_loader.return_value.load.return_value = expected_docs

        result = load_pdf_file("data/")

        mock_loader.assert_called_once_with(
            "data/",
            glob="*.pdf",
            loader_cls=mocker.ANY,
        )
        assert result == expected_docs
