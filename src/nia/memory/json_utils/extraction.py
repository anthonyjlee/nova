"""JSON extraction utilities."""

import logging
import asyncio
import json
import aiohttp
import re
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

def extract_valid_json(text: str, model: Optional[str] = None) -> Dict:
    """Extract and validate JSON from any text, handling common issues."""
    start_time = datetime.now()
    parse_attempts = []
    
    if model:
        logger.debug(f"Extracting JSON with model context: {model}")
        original_length = len(text)
        logger.debug(f"Original text length: {original_length}")
        
        if "llama" in model.lower():
            text = text.replace("```json", "").replace("```", "")
            logger.debug("Applied LLaMA markdown cleanup")
        elif "mistral" in model.lower():
            if "{" in text:
                text = text[text.index("{"):]
                logger.debug("Applied Mistral reasoning cleanup")
        elif "mixtral" in model.lower():
            text = text.replace("```json", "").replace("```", "")
            if "{" in text:
                text = text[text.index("{"):]
                logger.debug("Applied Mixtral combined cleanup")
        elif "phi" in model.lower():
            if "{" in text and "}" in text:
                start = text.index("{")
                end = text.rindex("}") + 1
                text = text[start:end]
                logger.debug("Applied Phi natural language cleanup")
        elif "openchat" in model.lower():
            if "assistant" in text.lower() and "{" in text:
                text = text[text.index("{"):]
                logger.debug("Applied OpenChat prefix cleanup")
        elif "codellama" in model.lower():
            text = text.replace("```json", "").replace("```javascript", "").replace("```", "")
            logger.debug("Applied CodeLLaMA code block cleanup")
        elif "vicuna" in model.lower():
            if "assistant:" in text.lower() and "{" in text:
                text = text[text.index("{"):]
            logger.debug("Applied Vicuna marker cleanup")
            
        cleaned_length = len(text)
        if cleaned_length != original_length:
            logger.debug(f"Cleaned text length: {cleaned_length} (removed {original_length - cleaned_length} chars)")
    
    def log_attempt(method: str, error: Optional[Exception] = None, result: Optional[Dict] = None):
        """Log parsing attempt details."""
        duration = (datetime.now() - start_time).total_seconds()
        attempt = {
            "method": method,
            "duration": duration,
            "success": error is None and result is not None
        }
        if error:
            attempt["error"] = str(error)
        parse_attempts.append(attempt)

    def clean_json_string(s: str) -> str:
        """Clean up JSON string to handle common format issues."""
        s = re.sub(r'%[0-9.]*[diouxXeEfFgGcrs]', '', s)
        s = s.replace('\\"', '"').replace('\\n', '\n')
        s = re.sub(r'[^\x20-\x7E\n]', '', s)
        s = re.sub(r',(\s*[}\]])', r'\1', s)
        s = re.sub(r'([{,]\s*)(\w+)(:)', r'\1"\2"\3', s)
        return s

    def find_json_object(text: str) -> Optional[str]:
        """Find the first valid JSON object in text."""
        logger.debug(f"Searching for JSON object in text of length {len(text)}")
        concept_match = re.search(r'\{[^{]*"concepts"\s*:\s*\[.*?\][^}]*\}', text, re.DOTALL)
        if concept_match:
            return concept_match.group(0)
        
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json_match.group(0)
        
        return None

    def try_parse_json(text: str, method: str) -> Optional[Dict]:
        """Try to parse JSON with various cleanup attempts."""
        try:
            result = json.loads(text)
            log_attempt(f"{method}/direct", result=result)
            return result
        except json.JSONDecodeError as e:
            log_attempt(f"{method}/direct", error=e)
            
            cleaned = clean_json_string(text)
            if cleaned != text:
                try:
                    result = json.loads(cleaned)
                    log_attempt(f"{method}/cleaned", result=result)
                    return result
                except json.JSONDecodeError as e:
                    log_attempt(f"{method}/cleaned", error=e)
            
            try:
                text_no_trailing = re.sub(r',(\s*[\]}])', r'\1', text)
                if text_no_trailing != text:
                    try:
                        result = json.loads(text_no_trailing)
                        log_attempt(f"{method}/trailing", result=result)
                        return result
                    except json.JSONDecodeError:
                        pass
                
                text_quotes = text.replace("'", '"')
                if text_quotes != text:
                    try:
                        result = json.loads(text_quotes)
                        log_attempt(f"{method}/quotes", result=result)
                        return result
                    except json.JSONDecodeError:
                        pass
                
                text_whitespace = re.sub(r'"\s+([^"]+)\s+":', r'"\1":', text)
                if text_whitespace != text:
                    try:
                        result = json.loads(text_whitespace)
                        log_attempt(f"{method}/whitespace", result=result)
                        return result
                    except json.JSONDecodeError:
                        pass
                        
            except Exception as e:
                log_attempt(f"{method}/fixes", error=e)
            
            return None

    logger.debug(f"Processing text input of length {len(text)}")
    if len(text) > 100:
        logger.debug(f"Text preview: {text[:100]}...")

    try:
        response_obj = json.loads(text)
        log_attempt("full_response", result=response_obj)
        if "choices" in response_obj and isinstance(response_obj["choices"], list):
            for i, choice in enumerate(response_obj["choices"]):
                if "message" in choice and "content" in choice["message"]:
                    content = choice["message"]["content"]
                    result = try_parse_json(content, f"choice_{i}")
                    if result:
                        return result
    except json.JSONDecodeError as e:
        log_attempt("full_response", error=e)

    json_text = find_json_object(text)
    if json_text:
        result = try_parse_json(json_text, "json_object")
        if result:
            return result

    code_match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    if code_match:
        result = try_parse_json(code_match.group(1), "code_block")
        if result:
            return result

    logger.error("JSON extraction failed. Attempts:")
    for attempt in parse_attempts:
        logger.error(f"  Method: {attempt['method']}")
        logger.error(f"  Duration: {attempt['duration']:.3f}s")
        logger.error(f"  Success: {attempt['success']}")
        if "error" in attempt:
            logger.error(f"  Error: {attempt['error']}")
        logger.error("---")

    raise ValueError("Could not extract valid JSON from response")

async def get_lmstudio_model() -> Optional[str]:
    """Get the currently active LMStudio model."""
    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.get('http://localhost:1234/v1/models') as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if isinstance(data, list) and len(data) > 0:
                            model_id = data[0].get('id')
                            if model_id:
                                logger.info(f"Detected LMStudio model: {model_id}")
                                model_lower = model_id.lower()
                                if "llama" in model_lower:
                                    logger.debug("Detected LLaMA family model")
                                elif "mistral" in model_lower:
                                    logger.debug("Detected Mistral family model")
                                elif "mixtral" in model_lower:
                                    logger.debug("Detected Mixtral family model")
                                elif "phi" in model_lower:
                                    logger.debug("Detected Phi family model")
                                elif "openchat" in model_lower:
                                    logger.debug("Detected OpenChat family model")
                                elif "vicuna" in model_lower:
                                    logger.debug("Detected Vicuna family model")
                                elif "codellama" in model_lower:
                                    logger.debug("Detected CodeLLaMA family model")
                                return model_id
                    elif resp.status == 404:
                        logger.warning("LMStudio API endpoint not found")
                    else:
                        logger.warning(f"Unexpected LMStudio API status: {resp.status}")
                    return None
            except aiohttp.ClientConnectorError:
                logger.warning("LMStudio not running or unreachable")
                return None
    except asyncio.TimeoutError:
        logger.warning("LMStudio API request timed out")
        return None
    except Exception as e:
        logger.error(f"Failed to get LMStudio model: {str(e)}")
        return None

def extract_json_from_lmstudio(response: str) -> Dict:
    """Extract and validate JSON from LLM response."""
    try:
        model = asyncio.run(get_lmstudio_model())
        if model:
            logger.info(f"Parsing response from LMStudio model: {model}")
        return extract_valid_json(response, model)
    except Exception as e:
        logger.error(f"Error extracting JSON from response: {str(e)}")
        raise ValueError(f"Failed to extract valid JSON: {str(e)}")
