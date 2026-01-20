"""
LLM client for AI-powered insights generation.

Supports:
- OpenAI API (GPT models)
- AWS Bedrock (Claude models)

Configuration via .env file:
- OPENAI_API_KEY: OpenAI API key
- AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION: AWS credentials
- LLM_PROVIDER: "openai" or "bedrock" (default: openai)
- OPENAI_MODEL: OpenAI model to use (default: gpt-4o-mini)
- BEDROCK_MODEL: Bedrock model to use (default: anthropic.claude-3-haiku-20240307-v1:0)
"""

import os
import json
import re
from pathlib import Path
from typing import Optional

# Load environment variables from .env file
from dotenv import load_dotenv

# Look for .env in project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Configuration from environment
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
BEDROCK_MODEL = os.environ.get("BEDROCK_MODEL", "anthropic.claude-3-haiku-20240307-v1:0")


def get_openai_client():
    """Get OpenAI client if API key is available."""
    try:
        from openai import OpenAI
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            return OpenAI(api_key=api_key)
    except ImportError:
        pass
    return None


def get_bedrock_client():
    """Get AWS Bedrock client if credentials are available."""
    try:
        import boto3
        # Check if AWS credentials are available
        session = boto3.Session()
        if session.get_credentials():
            return session.client(
                service_name="bedrock-runtime",
                region_name=os.environ.get("AWS_REGION", "us-east-1")
            )
    except Exception:
        pass
    return None


def call_openai(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1000,
) -> str:
    """Call OpenAI API."""
    client = get_openai_client()
    if not client:
        raise RuntimeError("OpenAI API key not configured")

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=model or OPENAI_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return response.choices[0].message.content


def call_bedrock_claude(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1000,
) -> str:
    """Call Claude via AWS Bedrock."""
    client = get_bedrock_client()
    if not client:
        raise RuntimeError("AWS Bedrock credentials not configured")

    messages = [{"role": "user", "content": prompt}]

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
    }

    if system_prompt:
        body["system"] = system_prompt

    response = client.invoke_model(
        modelId=model or BEDROCK_MODEL,
        body=json.dumps(body),
    )

    response_body = json.loads(response["body"].read())
    return response_body["content"][0]["text"]


def generate_insight(
    prompt: str,
    system_prompt: Optional[str] = None,
    prefer_provider: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1000,
) -> str:
    """
    Generate AI insight using available LLM provider.

    Args:
        prompt: The prompt to send
        system_prompt: Optional system context
        prefer_provider: "openai" or "bedrock" (defaults to LLM_PROVIDER env var)
        temperature: Sampling temperature
        max_tokens: Max response length

    Returns:
        Generated text response
    """
    provider = prefer_provider or LLM_PROVIDER

    # Try preferred provider first, then fallback to other
    errors = []

    if provider == "openai":
        try:
            return call_openai(prompt, system_prompt, temperature=temperature, max_tokens=max_tokens)
        except Exception as e:
            errors.append(f"OpenAI: {e}")
        try:
            return call_bedrock_claude(prompt, system_prompt, temperature=temperature, max_tokens=max_tokens)
        except Exception as e:
            errors.append(f"Bedrock: {e}")
    else:
        try:
            return call_bedrock_claude(prompt, system_prompt, temperature=temperature, max_tokens=max_tokens)
        except Exception as e:
            errors.append(f"Bedrock: {e}")
        try:
            return call_openai(prompt, system_prompt, temperature=temperature, max_tokens=max_tokens)
        except Exception as e:
            errors.append(f"OpenAI: {e}")

    # No LLM available - raise error
    raise RuntimeError(f"No LLM provider available. Errors: {'; '.join(errors)}")


def generate_dashboard_insight(metrics: dict) -> str:
    """Generate AI insight for dashboard metrics."""
    system_prompt = """You are an expert event analytics advisor helping race directors understand their event data.
    Provide brief, actionable insights (2-3 sentences max) based on the metrics provided.
    Focus on one key insight and one actionable recommendation.
    Be specific and reference actual numbers when helpful."""

    prompt = f"""Based on these event metrics, provide a brief insight:

Metrics:
{json.dumps(metrics, indent=2, default=str)}

Provide a short insight (2-3 sentences) with one actionable recommendation."""

    return generate_insight(prompt, system_prompt, temperature=0.7, max_tokens=200)


def generate_query_response(query: str, results: str, context: str) -> str:
    """Generate natural language response for a data query."""
    system_prompt = """You are a helpful event analytics assistant. The user has asked a question about their event data.
    Provide a clear, conversational summary of the query results.
    If appropriate, suggest follow-up questions or actions they might take.
    Keep responses concise but informative."""

    prompt = f"""User question: {query}

Data context: {context}

Query results:
{results}

Provide a helpful summary of these results in 2-4 sentences."""

    return generate_insight(prompt, system_prompt, temperature=0.5, max_tokens=300)


def generate_reengagement_message(participant_name: str, last_category: str, years_attended: list) -> str:
    """Generate personalized re-engagement message for churned participant."""
    system_prompt = """You are helping a race director write a personal outreach message to a past participant who hasn't registered recently.
    Write a warm, personal message that:
    - Acknowledges their past participation
    - Creates FOMO about upcoming events
    - Includes a clear call to action
    Keep it brief (3-4 sentences), friendly, and authentic."""

    prompt = f"""Write a re-engagement message for:
- Name: {participant_name}
- Previously raced in: {last_category}
- Years attended: {', '.join(map(str, years_attended))}

Write a brief, warm message to encourage them to return."""

    return generate_insight(prompt, system_prompt, temperature=0.8, max_tokens=150)


def translate_natural_query(query: str, schema_context: str) -> str:
    """
    Translate natural language query to pandas code.

    Returns executable Python code string.
    """
    system_prompt = """You are a data analyst assistant that translates natural language questions into pandas code.
    The user has a DataFrame called 'df' with event registration data.

    IMPORTANT: Return ONLY the pandas code, no explanations. The code should:
    - Be a single expression or a few lines that can be exec'd
    - Store the result in a variable called 'result'
    - DO NOT use import statements - pd (pandas), np (numpy), and math are already available
    - Use np.radians, np.sin, np.cos, np.sqrt etc for math operations instead of importing math functions

    Available variables:
    - df: the DataFrame with event data
    - pd: pandas library
    - np: numpy library
    - math: math library

    Example outputs:
    - result = df.groupby('participant_id').size().reset_index(name='count')
    - result = df[df['event_year'] == 2024]['participant_id'].nunique()
    """

    prompt = f"""DataFrame schema and sample:
{schema_context}

User question: {query}

Write pandas code to answer this question. Store the result in a variable called 'result'.
Return ONLY the code, nothing else."""

    response = generate_insight(prompt, system_prompt, temperature=0.3, max_tokens=500)

    # Clean up response - extract just the code
    code = response.strip()
    # Remove markdown code blocks if present
    code = re.sub(r'^```python\s*', '', code)
    code = re.sub(r'^```\s*', '', code)
    code = re.sub(r'\s*```$', '', code)

    return code.strip()


if __name__ == "__main__":
    print("=== LLM Configuration ===")
    print(f"Provider: {LLM_PROVIDER}")
    print(f"OpenAI Model: {OPENAI_MODEL}")
    print(f"Bedrock Model: {BEDROCK_MODEL}")

    print("\n=== Testing LLM Connection ===")
    try:
        response = generate_insight("Say 'Hello, the LLM connection is working!' in exactly those words.")
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n=== Dashboard Insight Test ===")
    test_metrics = {
        "total_participants": {"2023": 287, "2024": 342, "change_pct": 19.2},
        "retention_rate": 58,
        "revenue": {"2023": 8610, "2024": 10260},
    }
    try:
        print(generate_dashboard_insight(test_metrics))
    except Exception as e:
        print(f"Error: {e}")
