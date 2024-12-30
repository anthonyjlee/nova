import pytest
import gradio as gr
from nia.ui.mobile import MobileUI

def test_chatbot_initialization():
    """Test that chatbot components initialize with correct message format."""
    ui = MobileUI()
    
    # Create a test block to initialize components
    with gr.Blocks() as demo:
        chatbot = gr.Chatbot(
            type="messages",
            value=[
                {"role": "assistant", "content": "Test message"}
            ]
        )
    
    # Verify initial message format
    assert len(chatbot.value) == 1
    assert chatbot.value[0]["role"] == "assistant"
    assert chatbot.value[0]["content"] == "Test message"

@pytest.mark.asyncio
async def test_handle_command():
    """Test command handling with message format."""
    ui = MobileUI()
    
    # Test chat history
    chatbot = [
        {"role": "assistant", "content": "Hello!"}
    ]
    
    # Mock API key
    api_key = "mock_key"
    
    # Test message
    message = "Test message"
    
    # Handle command
    empty_msg, updated_chat = await ui.handle_command(message, api_key, chatbot)
    
    # Verify message was added
    assert len(updated_chat) >= 2  # Original + user message (+ possible error message)
    assert updated_chat[1]["role"] == "user"
    assert updated_chat[1]["content"] == "Test message"

@pytest.mark.asyncio
async def test_handle_chat():
    """Test chat handling with message format."""
    ui = MobileUI()
    
    # Test chat history
    history = [
        {"role": "assistant", "content": "Hello!"}
    ]
    
    # Test message
    message = "Test message"
    
    # Handle chat
    empty_msg, updated_history = await ui.handle_chat(message, history)
    
    # Verify message format
    assert len(updated_history) > 0
    for msg in updated_history:
        assert isinstance(msg, dict)
        assert "role" in msg
        assert "content" in msg
        assert msg["role"] in ["user", "assistant"]

def test_switch_chat():
    """Test chat switching with message format."""
    ui = MobileUI()
    
    # Switch to test chat
    title, status, history = ui.switch_chat("Test Chat")
    
    # Verify welcome message format
    assert len(history) == 1
    assert isinstance(history[0], dict)
    assert history[0]["role"] == "assistant"
    assert "Welcome to Test Chat" in history[0]["content"]

if __name__ == "__main__":
    pytest.main(["-v", "test_mobile_chat.py"])
