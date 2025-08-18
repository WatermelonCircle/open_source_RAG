"""
Test Claude Service

This test verifies that our Claude AI integration works correctly:
1. Service initialization with API key validation
2. RAG prompt creation and context building
3. Source citation formatting
4. Error handling for API failures

Why this test is important:
- Ensures Claude service initializes correctly
- Verifies prompt engineering for RAG works
- Tests source citation functionality
- Validates error handling without making API calls

We use mocks to test without requiring actual Claude API calls.
"""

import pytest
from unittest.mock import Mock, patch
from app.claude_service import ClaudeService
from app.models import ChatResponse
from app.config import settings

@pytest.fixture
def mock_context_docs():
    """Create mock context documents for testing"""
    return [
        {
            "text": "Python is a high-level programming language.",
            "filename": "python_guide.pdf",
            "page_number": 1,
            "similarity_score": 0.9
        },
        {
            "text": "FastAPI is a modern web framework for building APIs.",
            "filename": "fastapi_docs.pdf", 
            "page_number": 2,
            "similarity_score": 0.8
        }
    ]

def test_claude_service_initialization_without_api_key():
    """Test that ClaudeService requires API key"""
    # Temporarily clear the API key
    original_key = settings.CLAUDE_API_KEY
    settings.CLAUDE_API_KEY = ""
    
    try:
        with pytest.raises(ValueError, match="Claude API key is required"):
            ClaudeService()
    finally:
        # Restore original key
        settings.CLAUDE_API_KEY = original_key
    
    print("✅ Claude service correctly validates API key requirement")

@patch('app.claude_service.anthropic.Anthropic')
def test_claude_service_initialization_with_api_key(mock_anthropic):
    """Test that ClaudeService initializes with valid API key"""
    # Set a test API key
    settings.CLAUDE_API_KEY = "test-api-key"
    
    service = ClaudeService()
    
    assert service.client is not None
    mock_anthropic.assert_called_once_with(api_key="test-api-key")
    
    print("✅ Claude service initializes correctly with API key")

def test_build_context(mock_context_docs):
    """Test context building from document chunks"""
    # Mock the initialization to avoid API key requirement
    with patch('app.claude_service.anthropic.Anthropic'):
        settings.CLAUDE_API_KEY = "test-key"
        service = ClaudeService()
    
    context = service._build_context(mock_context_docs)
    
    # Check that context includes both documents
    assert "Python is a high-level programming language" in context
    assert "FastAPI is a modern web framework" in context
    assert "python_guide.pdf" in context
    assert "fastapi_docs.pdf" in context
    assert "Page 1" in context
    assert "Page 2" in context
    
    print("✅ Context building includes all document information")

def test_create_rag_prompt():
    """Test RAG prompt creation"""
    with patch('app.claude_service.anthropic.Anthropic'):
        settings.CLAUDE_API_KEY = "test-key"
        service = ClaudeService()
    
    query = "What is Python?"
    context = "Python is a programming language used for web development."
    
    prompt = service._create_rag_prompt(query, context)
    
    assert query in prompt
    assert context in prompt
    assert "CONTEXT:" in prompt
    assert "QUESTION:" in prompt
    assert "ANSWER:" in prompt
    assert "source documents" in prompt.lower()
    
    print("✅ RAG prompt includes all required components")

def test_format_sources(mock_context_docs):
    """Test source citation formatting"""
    with patch('app.claude_service.anthropic.Anthropic'):
        settings.CLAUDE_API_KEY = "test-key"
        service = ClaudeService()
    
    sources = service._format_sources(mock_context_docs)
    
    assert len(sources) == 2
    
    # Check first source
    assert sources[0]["filename"] == "python_guide.pdf"
    assert sources[0]["page"] == 1
    assert sources[0]["similarity_score"] == 0.9
    
    # Check second source
    assert sources[1]["filename"] == "fastapi_docs.pdf"
    assert sources[1]["page"] == 2
    assert sources[1]["similarity_score"] == 0.8
    
    print("✅ Source formatting preserves all metadata for citations")

def test_format_sources_removes_duplicates():
    """Test that duplicate sources are removed"""
    duplicate_docs = [
        {
            "text": "Text 1",
            "filename": "same_file.pdf",
            "page_number": 1,
            "similarity_score": 0.9
        },
        {
            "text": "Text 2", 
            "filename": "same_file.pdf",
            "page_number": 1,  # Same page as above
            "similarity_score": 0.8
        }
    ]
    
    with patch('app.claude_service.anthropic.Anthropic'):
        settings.CLAUDE_API_KEY = "test-key"
        service = ClaudeService()
    
    sources = service._format_sources(duplicate_docs)
    
    # Should only have one source despite duplicate page
    assert len(sources) == 1
    assert sources[0]["filename"] == "same_file.pdf"
    assert sources[0]["page"] == 1
    
    print("✅ Source formatting correctly removes duplicates")

@patch('app.claude_service.anthropic.Anthropic')
def test_generate_rag_response_no_context(mock_anthropic):
    """Test RAG response generation with no context documents"""
    settings.CLAUDE_API_KEY = "test-key"
    service = ClaudeService()
    
    response = service.generate_rag_response("What is Python?", [])
    
    assert isinstance(response, ChatResponse)
    assert "don't have any documents" in response.response
    assert len(response.sources) == 0
    assert response.timestamp is not None
    
    print("✅ Claude service handles empty context appropriately")

@patch('app.claude_service.anthropic.Anthropic')
def test_generate_rag_response_with_context(mock_anthropic, mock_context_docs):
    """Test RAG response generation with context"""
    settings.CLAUDE_API_KEY = "test-key"
    
    # Mock the API response
    mock_client = Mock()
    mock_response = Mock()
    mock_response.content = [Mock(text="Python is a programming language as mentioned in the documents.")]
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client
    
    service = ClaudeService()
    response = service.generate_rag_response("What is Python?", mock_context_docs)
    
    assert isinstance(response, ChatResponse)
    assert "Python is a programming language" in response.response
    assert len(response.sources) == 2
    assert response.timestamp is not None
    
    # Verify API was called with correct parameters
    mock_client.messages.create.assert_called_once()
    call_args = mock_client.messages.create.call_args
    assert call_args[1]["model"] == "claude-3-5-sonnet-20241022"
    assert call_args[1]["max_tokens"] == 1000
    
    print("✅ Claude service generates responses with proper structure and sources")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])