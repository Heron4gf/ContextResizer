from semantic_order import order_messages
from summarize import summarize

def resize(messages, max_tokens, query):
    # Handle both list of strings and list of message objects
    if messages and isinstance(messages[0], str):
        # List of strings
        content_list = messages
    else:
        # List of message objects
        content_list = [msg.get('content', '') for msg in messages]
    
    # Get ordered content based on semantic relevance
    ordered_content = order_messages(content_list, query)
    
    # Create a relevance score for each content item
    # The first item in ordered_content is most relevant (score 0), second is less relevant (score 1), etc.
    relevance_scores = {content: i for i, content in enumerate(ordered_content)}
    
    # For list of strings, just return the resized content
    if messages and isinstance(messages[0], str):
        for content in content_list:
            # Calculate max_size based on relevance score
            # More relevant (lower score) gets more tokens
            relevance_score = relevance_scores.get(content, len(ordered_content))
            max_size = max_tokens / (2 ** relevance_score)
            # Only process messages where max_size is at least 5
            if int(max_size) >= 5:
                summarized = summarize(content, int(max_size))
                if summarized:
                    yield summarized
                else:
                    yield content
    else:
        # For list of message objects, preserve the original order and roles
        for msg in messages:
            content = msg.get('content', '')
            # Calculate max_size based on relevance score
            # More relevant (lower score) gets more tokens
            relevance_score = relevance_scores.get(content, len(ordered_content))
            max_size = max_tokens / (2 ** relevance_score)
            # Only process messages where max_size is at least 5
            if int(max_size) >= 5:
                summarized = summarize(content, int(max_size))
                if summarized:
                    # Return the message with updated content
                    msg_copy = msg.copy()
                    msg_copy['content'] = summarized
                    yield msg_copy
                else:
                    yield msg

def auto_resize(context, max_tokens):
    """
    Resizes the context while keeping latest request and developer prompts intact.
    """
    import json
    
    # Parse JSONL context into list of message objects
    messages = [json.loads(line) for line in context.strip().split('\n') if line.strip()]
    
    # Get the latest message as query
    latest_message = messages[-1] if messages else {}
    query = latest_message.get('content', '')
    
    # Separate developer prompts from other messages
    developer_messages = [msg for msg in messages if msg.get('role') == 'developer']
    other_messages = [msg for msg in messages if msg.get('role') != 'developer']
    
    # Resize non-developer messages
    resized_messages_list = list(resize(other_messages, max_tokens, query))
    
    # Create a mapping from original content to resized messages
    content_to_resized = {}
    for resized_msg in resized_messages_list:
        content = resized_msg.get('content', '')
        # We need to match based on the original content, not the resized content
        # This is tricky because we've changed the content
        # Let's just use the order for now
        pass  # We'll handle this differently
    
    # Actually, let's just use the resized messages directly but preserve the original order
    # Create a mapping from original messages to resized messages based on order
    original_to_resized = {}
    for i, original_msg in enumerate(other_messages):
        if i < len(resized_messages_list):
            original_to_resized[id(original_msg)] = resized_messages_list[i]
    
    # Combine all messages, preserving original order and roles
    result = []
    for msg in messages:
        if msg.get('role') == 'developer':
            # Keep developer messages intact
            result.append(msg)
        elif id(msg) in original_to_resized:
            # Replace with resized message, preserving the original role
            resized_msg = original_to_resized[id(msg)]
            msg_copy = msg.copy()
            msg_copy['content'] = resized_msg.get('content', '')
            result.append(msg_copy)
        else:
            # Keep original if no resized version available
            result.append(msg)
    
    # Convert back to JSONL format
    return '\n'.join(json.dumps(msg) for msg in result)
