"""
Integration tests for backend/llm_factory.py - LLM factory with mocked dependencies.
"""
import pytest
from unittest.mock import patch, MagicMock


class TestGetUserLlm:
    """Tests for the get_user_llm function."""

    @pytest.mark.integration
    def test_returns_none_without_api_key(self, mock_streamlit):
        """Test that function returns None when no API key is available."""
        from backend.llm_factory import get_user_llm
        
        # No keys set in session state
        result = get_user_llm()
        assert result is None

    @pytest.mark.integration
    def test_creates_llm_with_user_credentials(self, mock_streamlit):
        """Test that function creates LLM with user-provided credentials."""
        from backend.llm_factory import get_user_llm
        
        mock_streamlit['session_state']['user_api_key'] = 'test-api-key'
        mock_streamlit['session_state']['user_model_name'] = 'gpt-4o'
        
        with patch('backend.llm_factory.ChatOpenAI') as mock_chat:
            mock_llm = MagicMock()
            mock_chat.return_value = mock_llm
            
            result = get_user_llm()
            
            assert result is mock_llm
            mock_chat.assert_called_once()
            call_kwargs = mock_chat.call_args[1]
            assert call_kwargs['api_key'] == 'test-api-key'
            assert call_kwargs['model'] == 'gpt-4o'
            assert call_kwargs['temperature'] == 0

    @pytest.mark.integration
    def test_falls_back_to_system_credentials(self, mock_streamlit):
        """Test that function falls back to system credentials when user input is empty."""
        from backend.llm_factory import get_user_llm
        
        # No user credentials, but system credentials available
        mock_streamlit['session_state']['system_api_key'] = 'system-api-key'
        mock_streamlit['session_state']['system_model_name'] = 'gpt-4o'
        
        with patch('backend.llm_factory.ChatOpenAI') as mock_chat:
            mock_llm = MagicMock()
            mock_chat.return_value = mock_llm
            
            result = get_user_llm()
            
            assert result is mock_llm
            call_kwargs = mock_chat.call_args[1]
            assert call_kwargs['api_key'] == 'system-api-key'

    @pytest.mark.integration
    def test_includes_base_url_when_provided(self, mock_streamlit):
        """Test that base_url is included when provided."""
        from backend.llm_factory import get_user_llm
        
        mock_streamlit['session_state']['user_api_key'] = 'test-api-key'
        mock_streamlit['session_state']['user_model_name'] = 'gpt-4o'
        mock_streamlit['session_state']['user_base_url'] = 'https://custom.api.com'
        
        with patch('backend.llm_factory.ChatOpenAI') as mock_chat:
            mock_llm = MagicMock()
            mock_chat.return_value = mock_llm
            
            result = get_user_llm()
            
            call_kwargs = mock_chat.call_args[1]
            assert call_kwargs['base_url'] == 'https://custom.api.com'

    @pytest.mark.integration
    def test_excludes_base_url_when_empty(self, mock_streamlit):
        """Test that base_url is excluded when empty string."""
        from backend.llm_factory import get_user_llm
        
        mock_streamlit['session_state']['user_api_key'] = 'test-api-key'
        mock_streamlit['session_state']['user_model_name'] = 'gpt-4o'
        mock_streamlit['session_state']['user_base_url'] = ''
        
        with patch('backend.llm_factory.ChatOpenAI') as mock_chat:
            mock_llm = MagicMock()
            mock_chat.return_value = mock_llm
            
            result = get_user_llm()
            
            call_kwargs = mock_chat.call_args[1]
            assert 'base_url' not in call_kwargs

    @pytest.mark.integration
    def test_defaults_model_name_to_gpt4o(self, mock_streamlit):
        """Test that model name defaults to gpt-4o when not specified."""
        from backend.llm_factory import get_user_llm
        
        mock_streamlit['session_state']['user_api_key'] = 'test-api-key'
        # No model name set
        
        with patch('backend.llm_factory.ChatOpenAI') as mock_chat:
            mock_llm = MagicMock()
            mock_chat.return_value = mock_llm
            
            result = get_user_llm()
            
            call_kwargs = mock_chat.call_args[1]
            assert call_kwargs['model'] == 'gpt-4o'

    @pytest.mark.integration
    def test_handles_exception_gracefully(self, mock_streamlit):
        """Test that function handles ChatOpenAI exceptions."""
        from backend.llm_factory import get_user_llm
        
        mock_streamlit['session_state']['user_api_key'] = 'test-api-key'
        mock_streamlit['session_state']['user_model_name'] = 'gpt-4o'
        
        with patch('backend.llm_factory.ChatOpenAI') as mock_chat:
            mock_chat.side_effect = Exception("API Error")
            
            result = get_user_llm()
            
            assert result is None
            mock_streamlit['error'].assert_called()

    @pytest.mark.integration
    def test_user_credentials_override_system(self, mock_streamlit):
        """Test that user credentials take priority over system credentials."""
        from backend.llm_factory import get_user_llm
        
        mock_streamlit['session_state']['system_api_key'] = 'system-key'
        mock_streamlit['session_state']['user_api_key'] = 'user-key'
        mock_streamlit['session_state']['user_model_name'] = 'gpt-4o'
        
        with patch('backend.llm_factory.ChatOpenAI') as mock_chat:
            mock_llm = MagicMock()
            mock_chat.return_value = mock_llm
            
            result = get_user_llm()
            
            call_kwargs = mock_chat.call_args[1]
            assert call_kwargs['api_key'] == 'user-key'
