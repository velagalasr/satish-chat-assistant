"""
Tools for ReAct Agent Framework
Defines available tools that agents can use.
"""

from typing import List, Optional, Dict, Any
from langchain_core.tools import Tool
from langchain_core.documents import Document
import os
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Optional import for Tavily search
try:
    from langchain_community.tools.tavily_search import TavilySearchResults
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False

from ..utils import get_logger

logger = get_logger(__name__)


def create_rag_search_tool(rag_retriever) -> Optional[Tool]:
    """
    Create a tool for searching the knowledge base using RAG.
    
    Args:
        rag_retriever: RAG retriever instance
        
    Returns:
        Tool instance or None if RAG not available
    """
    if not rag_retriever:
        return None
    
    def search_knowledge_base(query: str) -> str:
        """Search the knowledge base for relevant information."""
        try:
            docs = rag_retriever.invoke(query)
            if not docs:
                return "No relevant information found in the knowledge base."
            
            # Format results
            results = []
            for i, doc in enumerate(docs, 1):
                results.append(f"[Result {i}]\n{doc.page_content}\n")
            
            return "\n".join(results)
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return f"Error searching knowledge base: {str(e)}"
    
    return Tool(
        name="search_knowledge_base",
        description="Search the internal knowledge base for information about products, policies, documentation, and other company information. Use this when you need specific information from company documents.",
        func=search_knowledge_base
    )


def create_web_search_tool() -> Optional[Tool]:
    """
    Create a tool for searching the web using Tavily.
    Optional tool - only available if TAVILY_API_KEY is set.
    
    Returns:
        Tool instance or None if API key not available
    """
    if not TAVILY_AVAILABLE:
        logger.info("Tavily is not installed. Web search tool is disabled. Install with: pip install tavily-python")
        return None
    
    if not os.getenv("TAVILY_API_KEY"):
        logger.info("TAVILY_API_KEY not set. Web search tool is disabled (this is optional).")
        return None
    
    try:
        tavily_search = TavilySearchResults(max_results=3)
        return Tool(
            name="web_search",
            description="Search the internet for current information, news, or facts not in the knowledge base. Use this for up-to-date information or topics outside the internal documentation.",
            func=tavily_search.run
        )
    except Exception as e:
        logger.error(f"Error creating web search tool: {e}")
        return None


def create_calculator_tool() -> Tool:
    """
    Create a simple calculator tool.
    
    Returns:
        Tool instance
    """
    def calculate(expression: str) -> str:
        """Evaluate a mathematical expression."""
        try:
            # Safe evaluation of math expressions
            # Remove any dangerous characters
            allowed_chars = set("0123456789+-*/(). ")
            if not all(c in allowed_chars for c in expression):
                return "Invalid expression. Only numbers and basic operators (+, -, *, /, parentheses) are allowed."
            
            result = eval(expression, {"__builtins__": {}}, {})
            return f"The result is: {result}"
        except Exception as e:
            return f"Error calculating: {str(e)}"
    
    return Tool(
        name="calculator",
        description="Calculate mathematical expressions. Input should be a valid mathematical expression like '2 + 2' or '(10 * 5) + 3'.",
        func=calculate
    )


def create_email_tool(email_config: Optional[Dict[str, Any]] = None) -> Optional[Tool]:
    """
    Create an email sending tool with configurable whitelist.
    Supports SMTP and SendGrid.
    
    Args:
        email_config: Email configuration dictionary
        
    Returns:
        Tool instance or None if not configured
    """
    if not email_config or not email_config.get('enabled', False):
        logger.info("Email tool disabled in configuration")
        return None
    
    # Get configuration
    provider = email_config.get('provider', 'smtp')  # smtp or sendgrid
    allowed_recipients = email_config.get('allowed_recipients', [])
    allow_any = email_config.get('allow_any_email', False)
    from_email = email_config.get('from_email', '')
    from_name = email_config.get('from_name', 'Chatbot Assistant')
    
    # Validate configuration
    if not from_email:
        logger.error("Email tool: from_email not configured")
        return None
    
    def send_email(input_str: str) -> str:
        """
        Send an email. Input format: 'to: email@example.com, subject: Subject, body: Message body'
        or simplified: 'Send email to email@example.com about [subject] with message: [body]'
        """
        try:
            # Parse email components from natural language or structured format
            to_email = None
            subject = None
            body = None
            
            # Try to extract email address
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            email_matches = re.findall(email_pattern, input_str)
            if email_matches:
                to_email = email_matches[0]
            
            # Try structured format first
            if 'to:' in input_str.lower():
                parts = input_str.split(',')
                for part in parts:
                    part = part.strip()
                    if part.lower().startswith('to:'):
                        potential_email = part[3:].strip()
                        email_match = re.search(email_pattern, potential_email)
                        if email_match:
                            to_email = email_match.group(0)
                    elif part.lower().startswith('subject:'):
                        subject = part[8:].strip()
                    elif part.lower().startswith('body:'):
                        body = part[5:].strip()
            
            # Try natural language extraction
            if not subject:
                subject_match = re.search(r'(?:subject|about|regarding)[:\s]+([^,\.]+)', input_str, re.IGNORECASE)
                if subject_match:
                    subject = subject_match.group(1).strip()
            
            if not body:
                body_match = re.search(r'(?:body|message|content|text)[:\s]+(.+)$', input_str, re.IGNORECASE | re.DOTALL)
                if body_match:
                    body = body_match.group(1).strip()
                else:
                    # Use remaining text as body
                    body = input_str
            
            # Validate required fields
            if not to_email:
                return "Error: Could not extract recipient email address. Please specify a valid email address."
            
            if not subject:
                subject = "Message from Chatbot"
            
            if not body:
                return "Error: Email body is empty. Please provide the message content."
            
            # Check if recipient is allowed
            if not allow_any:
                # Check against whitelist (case-insensitive)
                allowed_lower = [email.lower() for email in allowed_recipients]
                if to_email.lower() not in allowed_lower:
                    return f"Error: Sending email to '{to_email}' is not allowed. Allowed recipients: {', '.join(allowed_recipients)}"
            
            # Send email based on provider
            if provider == 'smtp':
                return _send_smtp_email(to_email, subject, body, from_email, from_name, email_config)
            elif provider == 'sendgrid':
                return _send_sendgrid_email(to_email, subject, body, from_email, from_name, email_config)
            else:
                return f"Error: Unknown email provider '{provider}'"
                
        except Exception as e:
            logger.error(f"Error sending email: {e}", exc_info=True)
            return f"Error sending email: {str(e)}"
    
    description = f"Send emails to recipients. Allowed recipients: {', '.join(allowed_recipients) if not allow_any else 'any valid email'}. "
    description += "Provide the recipient email, subject, and message body. Example: 'Send email to john@example.com about Meeting Reminder with message: Don't forget our 2pm meeting'"
    
    return Tool(
        name="send_email",
        description=description,
        func=send_email
    )


def _send_smtp_email(
    to_email: str,
    subject: str,
    body: str,
    from_email: str,
    from_name: str,
    config: Dict[str, Any]
) -> str:
    """
    Send email via SMTP.
    """
    try:
        smtp_host = config.get('smtp_host', os.getenv('SMTP_HOST', 'smtp.gmail.com'))
        smtp_port = config.get('smtp_port', int(os.getenv('SMTP_PORT', '587')))
        smtp_user = config.get('smtp_user', os.getenv('SMTP_USER', from_email))
        smtp_password = os.getenv('SMTP_PASSWORD')
        
        if not smtp_password:
            return "Error: SMTP_PASSWORD environment variable not set"
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{from_name} <{from_email}>"
        msg['To'] = to_email
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        logger.info(f"Email sent successfully to {to_email}")
        return f"✅ Email sent successfully to {to_email} with subject '{subject}'"
        
    except Exception as e:
        logger.error(f"SMTP error: {e}")
        return f"Error sending via SMTP: {str(e)}"


def _send_sendgrid_email(
    to_email: str,
    subject: str,
    body: str,
    from_email: str,
    from_name: str,
    config: Dict[str, Any]
) -> str:
    """
    Send email via SendGrid API.
    """
    try:
        import requests
        
        api_key = os.getenv('SENDGRID_API_KEY')
        if not api_key:
            return "Error: SENDGRID_API_KEY environment variable not set"
        
        url = "https://api.sendgrid.com/v3/mail/send"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": from_email, "name": from_name},
            "subject": subject,
            "content": [{"type": "text/plain", "value": body}]
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 202:
            logger.info(f"Email sent successfully to {to_email} via SendGrid")
            return f"✅ Email sent successfully to {to_email} with subject '{subject}'"
        else:
            logger.error(f"SendGrid error: {response.status_code} - {response.text}")
            return f"Error from SendGrid: {response.status_code}"
            
    except ImportError:
        return "Error: 'requests' library not installed. Run: pip install requests"
    except Exception as e:
        logger.error(f"SendGrid error: {e}")
        return f"Error sending via SendGrid: {str(e)}"


def get_available_tools(rag_retriever=None, include_web_search: bool = False, email_config: Optional[Dict[str, Any]] = None) -> List[Tool]:
    """
    Get list of available tools for agents.
    
    Args:
        rag_retriever: Optional RAG retriever for knowledge base search
        include_web_search: Whether to include web search tool (requires TAVILY_API_KEY)
        email_config: Optional email configuration for email tool
        
    Returns:
        List of Tool instances
    """
    tools = []
    
    # Add RAG search tool if available
    rag_tool = create_rag_search_tool(rag_retriever)
    if rag_tool:
        tools.append(rag_tool)
        logger.info("Added knowledge base search tool")
    
    # Add web search tool if requested and API key is available
    if include_web_search:
        web_tool = create_web_search_tool()
        if web_tool:
            tools.append(web_tool)
            logger.info("Added web search tool")
        else:
            logger.warning("Web search requested but TAVILY_API_KEY not found - skipping")
    
    # Add calculator tool
    tools.append(create_calculator_tool())
    logger.info("Added calculator tool")
    
    # Add email tool if configured
    if email_config:
        email_tool = create_email_tool(email_config)
        if email_tool:
            tools.append(email_tool)
            logger.info("Added email tool")
    
    logger.info(f"Total tools available: {len(tools)}")
    return tools


def get_individual_tools(
    rag_retriever=None,
    enable_calculator: bool = False,
    enable_rag_search: bool = False,
    enable_web_search: bool = False,
    enable_email: bool = False,
    email_config: Optional[Dict[str, Any]] = None
) -> List[Tool]:
    """
    Get list of individually selected tools for agents.
    
    Args:
        rag_retriever: Optional RAG retriever for knowledge base search
        enable_calculator: Whether to include calculator tool
        enable_rag_search: Whether to include RAG search tool
        enable_web_search: Whether to include web search tool
        enable_email: Whether to include email tool
        email_config: Optional email configuration for email tool
        
    Returns:
        List of Tool instances
    """
    tools = []
    
    # Add calculator tool if enabled
    if enable_calculator:
        tools.append(create_calculator_tool())
        logger.info("Added calculator tool")
    
    # Add RAG search tool if enabled and available
    if enable_rag_search:
        rag_tool = create_rag_search_tool(rag_retriever)
        if rag_tool:
            tools.append(rag_tool)
            logger.info("Added knowledge base search tool")
        else:
            logger.warning("RAG search requested but retriever not available")
    
    # Add web search tool if enabled and API key is available
    if enable_web_search:
        web_tool = create_web_search_tool()
        if web_tool:
            tools.append(web_tool)
            logger.info("Added web search tool")
        else:
            logger.warning("Web search requested but TAVILY_API_KEY not found - skipping")
    
    # Add email tool if enabled and configured
    if enable_email:
        if email_config:
            email_tool = create_email_tool(email_config)
            if email_tool:
                tools.append(email_tool)
                logger.info("Added email tool")
        else:
            logger.warning("Email tool requested but configuration not provided")
    
    logger.info(f"Total tools available: {len(tools)}")
    return tools
