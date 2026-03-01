"""Utility functions for the application."""


def init_session_state():
    """Initialize session state with default values."""
    import streamlit as st
    import uuid
    
    defaults = {
        'stage': 0,
        'brief': {},
        'generated_content': {}
    }
    
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
    
    # Initialize item_id once, don't reinitialize it
    if 'current_item_id' not in st.session_state:
        st.session_state['current_item_id'] = str(uuid.uuid4())


def validate_sms_length(text, max_length=160):
    """Validate SMS text length."""
    if len(text) > max_length:
        return False, f"SMS přesahuje {max_length} znaků ({len(text)} znaků)"
    return True, "OK"


def validate_segment_id(segment_id):
    """Validate segment ID is not empty."""
    if not segment_id or not segment_id.strip():
        return False, "Segment ID nesmí být prázdný"
    return True, "OK"


def get_content_summary(content):
    """Get a summary of generated content for display."""
    return {
        "item_id": content.get('item_id'),
        "segment_id": content.get('segment_id'),
        "email_subject_length": len(content.get('email_subject', '')),
        "email_body_length": len(content.get('email_body', '')),
        "sms_length": len(content.get('sms_text', '')),
        "push_length": len(content.get('push_text', ''))
    }
