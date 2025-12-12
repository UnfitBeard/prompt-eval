# services/chatbot_service.py
import os
import time
import json
import asyncio
import requests
from datetime import datetime
from typing import List, Dict, Optional
from uuid import uuid4

from bs4 import BeautifulSoup
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import HumanMessage

import logging

logger = logging.getLogger(__name__)


class ChatbotService:
    def __init__(self, gemini_api_key: str):
        """
        Initialize the chatbot service with RAG capabilities.

        Args:
            gemini_api_key: Google Gemini API key
        """
        self.gemini_api_key = gemini_api_key

        # Configuration
        self.persist_dir = "./chroma_chatbot_db"
        self.collection_name = "prompt_engineering_knowledge"

        # Pre-defined knowledge base URLs
        self.knowledge_urls = [
            "https://learnprompting.org/",
            "https://promptingguide.ai/",
            "https://www.prompting101.com/",
            "https://huggingface.co/blog",
            "https://www.deeplearning.ai/blog",
            "https://platform.openai.com/docs/guides/prompt-engineering",
            "https://en.wikipedia.org/wiki/Prompt_engineering",
            "https://prompts.chat/",
            "https://www.anthropic.com/news",
            "https://cohere.com/blog"
        ]

        # Initialize components
        self.llm = None
        self.embeddings = None
        self.vectorstore = None
        self.rag_chain = None
        self.retriever = None

        # Conversation storage (in-memory, consider Redis for production)
        self.conversations = {}

        # Conversation storage file
        self.conversations_file = "./chatbot_conversations.json"
        self.conversations = self._load_conversations()

        # Initialize
        self.initialize()

    def initialize(self):
        """Initialize the chatbot service"""
        try:
            # Configure Gemini

            # Initialize LLM
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash-lite",
                temperature=0.7,
                google_api_key=self.gemini_api_key,
                max_tokens=1000,
                timeout=30
            )

            # Initialize embeddings (CPU-only)
            # NOTE: model_kwargs is supported by langchain_huggingface and is passed through to
            # the underlying embedding model.
            self.embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                # langchain_huggingface forwards model_kwargs directly into SentenceTransformer(..., **model_kwargs)
                # so we nest SentenceTransformer's own model_kwargs inside.
                model_kwargs={
                    "device": "cpu",
                    "model_kwargs": {"low_cpu_mem_usage": False},
                },
            )

            # Load or create vector store
            if os.path.exists(self.persist_dir):
                self.vectorstore = Chroma(
                    persist_directory=self.persist_dir,
                    embedding_function=self.embeddings,
                    collection_name=self.collection_name
                )
                logger.info(
                    f"Loaded existing knowledge base with {self.vectorstore._collection.count()} documents")
            else:
                self.vectorstore = Chroma(
                    persist_directory=self.persist_dir,
                    embedding_function=self.embeddings,
                    collection_name=self.collection_name
                )
                logger.info("Created new knowledge base")

            # Create retriever
            self.retriever = self.vectorstore.as_retriever(
                search_kwargs={"k": 3}
            )

            # Create RAG chain
            self._create_rag_chain()

            logger.info("Chatbot service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize chatbot service: {e}")
            raise

    def _create_rag_chain(self):
        """Create the RAG chain for question answering"""
        system_prompt = """You are an expert Prompt Engineering tutor named "PromptPro". 
You help users understand and improve their prompt engineering skills.

CONTEXT INFORMATION:
{context}

INSTRUCTIONS:
1. Use the provided context to answer questions accurately
2. If the context doesn't contain the answer, use your general knowledge but mention this
3. Be concise but thorough - aim for 2-3 paragraphs maximum
4. Use examples when helpful
5. Ask follow-up questions to better understand user needs
6. Format responses with clear paragraphs and use **bold** for key terms
7. If discussing code examples, use appropriate formatting
8. Always maintain a helpful, educational tone

Current conversation history:
{history}

Now answer the user's question:"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}")
        ])

        qa_chain = create_stuff_documents_chain(self.llm, prompt)
        self.rag_chain = create_retrieval_chain(self.retriever, qa_chain)

    async def scrape_and_index_urls(self, urls: List[str]) -> int:
        """
        Scrape URLs and add to knowledge base.

        Args:
            urls: List of URLs to scrape

        Returns:
            Number of successfully scraped URLs
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        all_docs = []

        for url in urls:
            try:
                # Fetch page
                response = requests.get(
                    url, headers=headers, timeout=15, verify=False)
                response.raise_for_status()

                # Parse with BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')

                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()

                # Extract text from relevant elements
                text_elements = []

                # Try to get main content
                main_content = soup.find('main') or soup.find(
                    'article') or soup.find('div', class_='content')
                if main_content:
                    text_elements.append(
                        main_content.get_text(separator=' ', strip=True))
                else:
                    # Fallback to all paragraphs and headings
                    for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']):
                        text = element.get_text(strip=True)
                        if text and len(text) > 50:
                            text_elements.append(text)

                if text_elements:
                    page_content = " ".join(text_elements)
                    # Clean up excessive whitespace
                    page_content = ' '.join(page_content.split())

                    doc = Document(
                        # Limit content length
                        page_content=page_content[:8000],
                        metadata={
                            "source": url,
                            "title": soup.title.string if soup.title else url,
                            "scraped_at": datetime.now().isoformat(),
                            "url": url
                        }
                    )
                    all_docs.append(doc)
                    logger.info(f"Successfully scraped: {url}")

            except Exception as e:
                logger.error(f"Failed to scrape {url}: {e}")

        if all_docs:
            # Split documents
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )

            split_docs = text_splitter.split_documents(all_docs)

            # Add to vector store
            if self.vectorstore:
                self.vectorstore.add_documents(split_docs)
                logger.info(
                    f"Added {len(split_docs)} document chunks to knowledge base")

        return len(all_docs)

    async def refresh_knowledge_base(self) -> Dict:
        """Refresh the knowledge base with latest content"""
        try:
            logger.info("Starting knowledge base refresh...")

            # Get existing URLs from vector store
            existing_urls = set()
            if self.vectorstore:
                existing_metadata = self.vectorstore.get()['metadatas']
                existing_urls = {
                    meta.get('url') for meta in existing_metadata if meta.get('url')}

            # Determine which URLs need to be scraped
            urls_to_scrape = [
                url for url in self.knowledge_urls if url not in existing_urls]

            if not urls_to_scrape:
                logger.info("All URLs already in knowledge base")
                return {
                    "status": "up_to_date",
                    "urls_scraped": 0,
                    "total_urls": len(self.knowledge_urls)
                }

            # Scrape new URLs
            count = await self.scrape_and_index_urls(urls_to_scrape)

            # Recreate RAG chain with updated vector store
            self._create_rag_chain()

            return {
                "status": "success",
                "urls_scraped": count,
                "total_urls": len(self.knowledge_urls),
                "message": f"Successfully updated knowledge base with {count} new sources"
            }

        except Exception as e:
            logger.error(f"Failed to refresh knowledge base: {e}")
            raise

    def get_knowledge_base_stats(self) -> Dict:
        """Get knowledge base statistics"""
        if not self.vectorstore:
            return {"status": "not_initialized"}

        try:
            count = self.vectorstore._collection.count()
            return {
                "status": "ready",
                "document_count": count,
                "collection": self.collection_name,
                "urls_configured": len(self.knowledge_urls),
                "vectorstore_path": self.persist_dir
            }
        except Exception as e:
            logger.error(f"Failed to get knowledge base stats: {e}")
            return {"status": "error", "error": str(e)}

    async def process_message(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        include_context: bool = True
    ) -> Dict:
        """
        Process a user message and generate response.

        Args:
            message: User's message
            conversation_id: Optional conversation ID
            include_context: Whether to use RAG context

        Returns:
            Dictionary with response and metadata
        """
        start_time = time.time()

        # Create or get conversation
        if not conversation_id or conversation_id not in self.conversations:
            conversation_id = str(uuid4())
            self.conversations[conversation_id] = {
                "id": conversation_id,
                "messages": [],
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "title": None
            }

        conversation = self.conversations[conversation_id]

        try:
            # Add user message to conversation
            user_message = {
                "role": "user",
                "content": message,
                "timestamp": datetime.now().isoformat()
            }
            conversation["messages"].append(user_message)

            # Prepare conversation history for context
            # Last 5 messages as context
            history_messages = conversation["messages"][-6:-1]
            history = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in history_messages
            ])

            # Generate response
            response_text = ""
            context_used = False
            sources = []

            if include_context and self.rag_chain:
                try:
                    # Get relevant context using RAG
                    result = self.rag_chain.invoke({
                        "input": message,
                        "history": history
                    })

                    response_text = result.get("answer", "").strip()
                    context_used = True

                    # Extract sources from context
                    if "context" in result:
                        docs = result.get("context", [])
                        sources = [
                            {
                                "source": doc.metadata.get("url", doc.metadata.get("source", "Unknown")),
                                "title": doc.metadata.get("title", "No title"),
                                "relevance": 0.8,  # Placeholder, could be calculated from similarity score
                                "snippet": doc.page_content[:200] + "..."
                            }
                            for doc in docs[:3]
                        ]

                except Exception as e:
                    logger.error(f"RAG chain failed: {e}")
                    # Fallback to direct LLM
                    response_text = await self._generate_fallback_response(message, history)
            else:
                # Direct LLM response
                response_text = await self._generate_fallback_response(message, history)

            # Generate follow-up suggestions
            suggestions = self._generate_suggestions(message, response_text)

            # Add assistant response to conversation
            assistant_message = {
                "role": "assistant",
                "content": response_text,
                "timestamp": datetime.now().isoformat()
            }
            conversation["messages"].append(assistant_message)
            conversation["updated_at"] = datetime.now()

            # Set conversation title from first message if not set
            if not conversation["title"] and len(conversation["messages"]) == 2:
                conversation["title"] = message[:50] + \
                    ("..." if len(message) > 50 else "")

            processing_time = (time.time() - start_time) * 1000

            self._save_conversations()

            return {
                "response": response_text,
                "conversation_id": conversation_id,
                "context_used": context_used,
                "suggestions": suggestions,
                "sources": sources,
                "processing_time_ms": round(processing_time, 2),
                "message_count": len(conversation["messages"])
            }

        except Exception as e:
            logger.error(f"Failed to process message: {e}", exc_info=True)
            raise

    async def _generate_fallback_response(self, message: str, history: str) -> str:
        """Generate response using LLM without RAG"""
        try:
            prompt = f"""You are an expert Prompt Engineering tutor named "PromptPro". 
You help users understand and improve their prompt engineering skills.

Previous conversation:
{history}

User's question: {message}

Provide a helpful, accurate response about prompt engineering. 
Be concise (2-3 paragraphs), use examples, and ask a follow-up question if appropriate."""

            response = await asyncio.wait_for(
                self.llm.ainvoke([HumanMessage(content=prompt)]),
                timeout=15.0
            )

            return response.content if response else "I'm having trouble responding. Please try again."

        except asyncio.TimeoutError:
            logger.error("LLM response timed out")
            return "I apologize for the delay. Please try your question again."
        except Exception as e:
            logger.error(f"Fallback response generation failed: {e}")
            return "I apologize, but I'm unable to generate a response right now. Please try again later."

    def _generate_suggestions(self, user_message: str, response: str) -> List[str]:
        """Generate follow-up suggestion questions"""
        suggestions = []

        # Analyze user message for topic
        message_lower = user_message.lower()

        topic_keywords = {
            "prompt": ["prompt", "template", "format"],
            "model": ["model", "llm", "gpt", "gemini", "claude"],
            "technique": ["technique", "method", "approach", "strategy"],
            "code": ["code", "programming", "python", "api", "function"],
            "evaluation": ["evaluate", "score", "metric", "quality", "test"]
        }

        # Add topic-specific suggestions
        for topic, keywords in topic_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                if topic == "prompt":
                    suggestions.extend([
                        "Can you show me an advanced prompt template?",
                        "How do I optimize prompts for different models?",
                        "What are common prompt patterns I should know?"
                    ])
                elif topic == "model":
                    suggestions.extend([
                        "How do prompts differ between models?",
                        "What are the limitations of current models?",
                        "How can I test prompts across different models?"
                    ])
                elif topic == "technique":
                    suggestions.extend([
                        "Can you explain chain-of-thought prompting?",
                        "What are few-shot vs zero-shot prompting?",
                        "How do I implement prompt chaining?"
                    ])
                elif topic == "code":
                    suggestions.extend([
                        "Show me a code example for prompt generation",
                        "How do I integrate prompts into my application?",
                        "What libraries are best for prompt engineering?"
                    ])
                elif topic == "evaluation":
                    suggestions.extend([
                        "What metrics should I use to evaluate prompts?",
                        "How do I A/B test different prompts?",
                        "What tools exist for prompt evaluation?"
                    ])
                break

        # Add generic suggestions if we have few
        if len(suggestions) < 3:
            suggestions.extend([
                "Can you give me a practical example?",
                "What are the best practices for this?",
                "How does this compare to other techniques?"
            ])

        # Remove duplicates and limit to 3
        return list(dict.fromkeys(suggestions))[:3]

    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Get a specific conversation"""
        return self.conversations.get(conversation_id)

    def list_conversations(self, limit: int = 20) -> List[Dict]:
        """List all conversations"""
        conversations = list(self.conversations.values())
        conversations.sort(key=lambda x: x["updated_at"], reverse=True)
        return conversations[:limit]

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False

    def _load_conversations(self) -> Dict:
        """Load conversations from file"""
        if os.path.exists(self.conversations_file):
            try:
                with open(self.conversations_file, 'r') as f:
                    data = json.load(f)
                    # Convert string dates back to datetime objects
                    for conv_id, conv in data.items():
                        if 'created_at' in conv:
                            conv['created_at'] = datetime.fromisoformat(
                                conv['created_at'])
                        if 'updated_at' in conv:
                            conv['updated_at'] = datetime.fromisoformat(
                                conv['updated_at'])
                    return data
            except Exception as e:
                logger.error(f"Failed to load conversations: {e}")
        return {}

    def _save_conversations(self):
        """Save conversations to file"""
        try:
            # Convert datetime objects to strings for JSON serialization
            data_to_save = {}
            for conv_id, conv in self.conversations.items():
                conv_copy = conv.copy()
                if 'created_at' in conv_copy:
                    conv_copy['created_at'] = conv_copy['created_at'].isoformat()
                if 'updated_at' in conv_copy:
                    conv_copy['updated_at'] = conv_copy['updated_at'].isoformat()
                data_to_save[conv_id] = conv_copy

            with open(self.conversations_file, 'w') as f:
                json.dump(data_to_save, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save conversations: {e}")

    # Also update delete_conversation method

    def delete_conversation(self, conversation_id: str) -> bool:
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            self._save_conversations()  # Save after deletion
            return True
        return False

    def clear_conversations(self) -> int:
        """Clear all conversations"""
        count = len(self.conversations)
        self.conversations.clear()
        return count

    async def ensure_knowledge_base(self) -> bool:
        """Ensure knowledge base has content, scrape if empty"""
        stats = self.get_knowledge_base_stats()

        if stats.get("status") == "ready" and stats.get("document_count", 0) > 0:
            return True

        logger.info(
            "Knowledge base is empty or not ready, scraping initial content...")
        try:
            # Start with first 3
            await self.scrape_and_index_urls(self.knowledge_urls[:3])
            self._create_rag_chain()  # Recreate chain with new content
            logger.info("Initial knowledge base content loaded")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize knowledge base: {e}")
            return False
