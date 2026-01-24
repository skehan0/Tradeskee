import json

async def process_streaming_response(response):
    """
    Process a streaming HTTP response asynchronously and yield parsed JSON content.
    """
    buffer = ""
    async for line in response.aiter_lines():
        if not line.strip():
            continue  # Skip empty lines
        
        # Add line to buffer
        buffer += line + "\n"
        
        # Try to parse complete JSON objects from buffer
        while buffer:
            try:
                # Find the end of a complete JSON object
                json_data = json.loads(buffer.strip())
                buffer = ""  # Reset buffer on successful parse
                
                # Extract content from the response
                if "message" in json_data and "content" in json_data["message"]:
                    content = json_data["message"]["content"]
                    if content:  # Only yield non-empty content
                        yield content
                elif "response" in json_data:  # Alternative response format
                    content = json_data["response"]
                    if content:
                        yield content
                break
                
            except json.JSONDecodeError as e:
                # If JSON is incomplete, try to find a complete object
                lines = buffer.strip().split('\n')
                parsed_any = False
                
                for i, line in enumerate(lines):
                    if line.strip():
                        try:
                            json_data = json.loads(line.strip())
                            # Extract content
                            if "message" in json_data and "content" in json_data["message"]:
                                content = json_data["message"]["content"]
                                if content:
                                    yield content
                            elif "response" in json_data:
                                content = json_data["response"]
                                if content:
                                    yield content
                            parsed_any = True
                        except json.JSONDecodeError:
                            continue
                
                # Keep remaining unparsed lines in buffer
                if parsed_any:
                    # Remove parsed lines, keep the rest
                    remaining_lines = []
                    for line in lines:
                        try:
                            json.loads(line.strip())
                        except:
                            remaining_lines.append(line)
                    buffer = '\n'.join(remaining_lines)
                else:
                    # Wait for more data
                    break