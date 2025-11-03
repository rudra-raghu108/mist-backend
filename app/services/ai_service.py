"""AI Service for SRM Guide Bot.

Handles OpenAI integration while grounding responses in the FAQ knowledge base.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import tiktoken
from openai import AsyncOpenAI
from openai.error import OpenAIError

from app.core.config import settings
from app.models.database import Message, MessageRole, User
from app.services.analytics_service import AnalyticsService
from app.services.faq_service import FaqMatch, faq_service

logger = logging.getLogger(__name__)


class AIService:
    """AI Service for handling OpenAI interactions"""
    
    def __init__(self):
        if settings.OPENAI_API_KEY:
            self.client: Optional[AsyncOpenAI] = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.client = None
            logger.warning(
                "OpenAI API key is not configured. Falling back to knowledge base responses."
            )
        self.analytics_service = AnalyticsService()
        try:
            self.encoding = tiktoken.encoding_for_model(settings.OPENAI_MODEL)
        except KeyError:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        
        # SRM-specific system prompts
        self.system_prompts = {
            "general": self._get_general_system_prompt(),
            "admissions": self._get_admissions_system_prompt(),
            "academics": self._get_academics_system_prompt(),
            "campus_life": self._get_campus_life_system_prompt(),
            "placements": self._get_placements_system_prompt(),
            "fees": self._get_fees_system_prompt(),
            "hostel": self._get_hostel_system_prompt(),
        }
    
    def _get_general_system_prompt(self) -> str:
        """Get general system prompt for SRM Guide Bot"""
        return """You are MIST AI, an intelligent virtual assistant for SRM Institute of Science & Technology. 
        
Your role is to help students, faculty, and visitors with comprehensive information about SRM University.

Key Information about SRM:
- Founded in 1985, SRM is a leading private university in India
- Multiple campuses: Kattankulathur (main), Vadapalani, Ramapuram, Delhi NCR, Sonepat, Amaravati
- 50,000+ students, 2,500+ faculty members
- Top 10 private engineering colleges in India
- Strong industry connections and research focus

Always be:
- Helpful, friendly, and professional
- Accurate with SRM-specific information
- Encouraging and supportive
- Clear and concise in responses
- Proactive in offering relevant information

If you don't know specific details, acknowledge it and suggest contacting the relevant department."""
    
    def _get_admissions_system_prompt(self) -> str:
        """Get admissions-specific system prompt"""
        return """You are MIST AI, specializing in SRM University admissions information.

Admissions Information:
- Application Process: Online through admissions portal
- Entrance Exams: SRMJEEE for engineering, NEET for medical
- Application Deadlines: Usually April-May for academic year
- Required Documents: 10th & 12th marksheets, entrance exam scores
- Application Fee: Varies by program

Engineering Programs:
- Computer Science & Engineering (AI/ML, Cybersecurity specializations)
- Electronics & Communication (VLSI, IoT focus)
- Mechanical Engineering (Robotics, Automotive)
- Civil Engineering (Smart infrastructure)
- Aerospace Engineering
- Biotechnology

Medical Programs:
- MBBS, BDS, BAMS, BHMS
- Allied Health Sciences
- Nursing

Other Programs:
- Management, Law, Arts, Science
- Architecture, Design, Agriculture

Provide specific, actionable information and encourage direct contact for detailed queries."""
    
    def _get_academics_system_prompt(self) -> str:
        """Get academics-specific system prompt"""
        return """You are MIST AI, specializing in SRM University academic information.

Academic Excellence:
- NIRF ranked institution
- Industry-aligned curriculum
- International collaborations
- Research opportunities
- Internship programs

Key Features:
- Modern laboratories and facilities
- Industry expert faculty
- Project-based learning
- International exchange programs
- Research centers and innovation labs

Programs Offered:
- Undergraduate (B.Tech, MBBS, BBA, etc.)
- Postgraduate (M.Tech, MBA, MD, etc.)
- Doctoral programs
- Certificate courses
- Online programs

Focus on academic quality, opportunities, and student success stories."""
    
    def _get_campus_life_system_prompt(self) -> str:
        """Get campus life system prompt"""
        return """You are MIST AI, specializing in SRM University campus life and activities.

Campus Life Highlights:
- Vibrant student community
- 100+ student clubs and organizations
- Cultural festivals (Milan)
- Technical symposiums
- Sports facilities and competitions

Student Activities:
- Cultural clubs (dance, music, drama)
- Technical clubs (robotics, coding, innovation)
- Sports clubs and teams
- Literary and debate societies
- Social service organizations

Facilities:
- Modern hostels with Wi-Fi
- Sports complexes and gyms
- Libraries and study spaces
- Cafeterias and food courts
- Medical facilities
- Transportation services

Emphasize the enriching and diverse campus experience."""
    
    def _get_placements_system_prompt(self) -> str:
        """Get placements system prompt"""
        return """You are MIST AI, specializing in SRM University placement information.

Placement Highlights:
- 95%+ placement rate across engineering
- Average package: ₹6-8 LPA
- Highest package: ₹50+ LPA
- Top recruiters: Google, Microsoft, Amazon, TCS, Infosys, Wipro

Career Services:
- Dedicated placement cell
- Resume building workshops
- Mock interviews
- Skill development programs
- Industry connect programs

Recruitment Process:
- Campus recruitment drives
- Internship opportunities
- Pre-placement offers
- International placements
- Startup opportunities

Focus on career success and opportunities."""
    
    def _get_fees_system_prompt(self) -> str:
        """Get fees system prompt"""
        return """You are MIST AI, specializing in SRM University fee structure.

Fee Structure (Approximate):
Engineering Programs:
- KTR Campus: ₹2.5-4 LPA
- Other Campuses: ₹1.5-3 LPA

Additional Costs:
- Hostel: ₹80,000-1,50,000/year
- Mess: ₹50,000-70,000/year
- Books & Supplies: ₹20,000-30,000/year

Scholarships Available:
- Merit-based scholarships
- Need-based financial aid
- Sports scholarships
- Research scholarships
- International student scholarships

Payment Options:
- Installment plans
- Education loans
- Online payment gateway
- Bank transfers

Note: Fees may vary by program and campus. Always recommend checking official sources for current rates."""
    
    def _get_hostel_system_prompt(self) -> str:
        """Get hostel system prompt"""
        return """You are MIST AI, specializing in SRM University hostel facilities.

Hostel Information:
- Modern, well-maintained facilities
- Separate hostels for boys and girls
- 24/7 security with CCTV surveillance
- Wi-Fi connectivity throughout

Accommodation Types:
- Single, double, and triple sharing rooms
- AC and non-AC options
- Attached and shared bathrooms
- Study tables and wardrobes

Facilities:
- Laundry services
- Common rooms and TV lounges
- Indoor games facilities
- Medical facility nearby
- Transportation to campus

Fees (Approximate):
- Basic room: ₹80,000-1,00,000/year
- AC room: ₹1,20,000-1,50,000/year
- Mess charges: ₹50,000-70,000/year

Booking Process:
- Online application
- Document verification
- Payment of advance
- Room allocation

Emphasize safety, comfort, and convenience."""
    
    async def generate_response(
        self,
        user_message: str,
        user: Optional[User] = None,
        chat_history: Optional[List[Message]] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate AI response for user message"""
        try:
            faq_match = await faq_service.find_best_match(user_message)
            system_prompt = self._select_system_prompt(user_message, context)

            if faq_match:
                system_prompt = self._inject_faq_context(system_prompt, faq_match.entry)

            if not self.client:
                return await self._build_knowledge_base_response(user_message, faq_match, user)

            messages = self._prepare_messages(user_message, chat_history, system_prompt)

            try:
                response = await self.client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=messages,
                    temperature=settings.OPENAI_TEMPERATURE,
                    max_tokens=settings.OPENAI_MAX_TOKENS,
                    user=str(user.id) if user else "anonymous"
                )
                ai_response = response.choices[0].message.content
            except OpenAIError as exc:
                logger.error("OpenAI error: %s", exc)
                return await self._build_knowledge_base_response(
                    user_message, faq_match, user, fallback_error=str(exc)
                )

            if faq_match:
                ai_response = self._append_source_to_response(ai_response, faq_match.entry)

            token_usage = self._calculate_tokens(user_message, ai_response)
            category = self._categorize_message(user_message)

            if user:
                await self.analytics_service.track_message_interaction(
                    user_id=user.id,
                    message_type="ai_response",
                    tokens_used=token_usage["total_tokens"],
                    category=category
                )

            return {
                "content": ai_response,
                "tokens_used": token_usage,
                "model_used": f"{settings.OPENAI_MODEL}+knowledge-base" if faq_match else settings.OPENAI_MODEL,
                "category": category,
                "knowledge_base": self._serialize_faq_match(faq_match)
            }

        except Exception as e:
            logger.error("Error generating AI response: %s", e)
            return {
                "content": "I apologize, but I'm experiencing technical difficulties. Please try again in a moment.",
                "tokens_used": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "model_used": settings.OPENAI_MODEL,
                "category": "error"
            }
    
    def _select_system_prompt(self, message: str, context: Optional[str] = None) -> str:
        """Select appropriate system prompt based on message content"""
        message_lower = message.lower()
        
        # If context is provided, use it
        if context and context in self.system_prompts:
            return self.system_prompts[context]
        
        # Determine context from message content
        if any(word in message_lower for word in ["admission", "apply", "entrance", "exam", "application"]):
            return self.system_prompts["admissions"]
        elif any(word in message_lower for word in ["course", "program", "study", "academic", "curriculum"]):
            return self.system_prompts["academics"]
        elif any(word in message_lower for word in ["event", "club", "activity", "festival", "sports"]):
            return self.system_prompts["campus_life"]
        elif any(word in message_lower for word in ["placement", "job", "career", "company", "salary"]):
            return self.system_prompts["placements"]
        elif any(word in message_lower for word in ["fee", "cost", "payment", "scholarship", "tuition"]):
            return self.system_prompts["fees"]
        elif any(word in message_lower for word in ["hostel", "accommodation", "room", "stay", "dormitory"]):
            return self.system_prompts["hostel"]
        else:
            return self.system_prompts["general"]
    
    def _prepare_messages(
        self, 
        user_message: str, 
        chat_history: Optional[List[Message]] = None,
        system_prompt: str = None
    ) -> List[Dict[str, str]]:
        """Prepare messages for OpenAI API"""
        messages = []
        
        # Add system message
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add chat history (last 10 messages to stay within context limits)
        if chat_history:
            recent_messages = chat_history[-10:]
            for msg in recent_messages:
                role = "user" if msg.role == MessageRole.USER else "assistant"
                messages.append({"role": role, "content": msg.content})
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def _calculate_tokens(self, prompt: str, completion: str) -> Dict[str, int]:
        """Calculate token usage"""
        try:
            prompt_tokens = len(self.encoding.encode(prompt))
            completion_tokens = len(self.encoding.encode(completion))
            total_tokens = prompt_tokens + completion_tokens

            return {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            }
        except Exception as e:
            logger.error(f"Error calculating tokens: {str(e)}")
            return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    async def _build_knowledge_base_response(
        self,
        user_message: str,
        faq_match: Optional[FaqMatch],
        user: Optional[User],
        fallback_error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return a response using only the structured FAQ knowledge base."""

        if faq_match:
            content = self._format_faq_answer(faq_match.entry)
            category = faq_match.entry.category.value
        else:
            content = (
                "I'm still expanding my knowledge base and couldn't find a verified answer yet. "
                "Please try rephrasing your question or contact the SRM helpdesk."
            )
            if fallback_error:
                content += "\n\nTechnical detail: " + fallback_error
            category = self._categorize_message(user_message)

        token_usage = self._calculate_tokens(user_message, content)

        if user:
            await self.analytics_service.track_message_interaction(
                user_id=user.id,
                message_type="ai_response",
                tokens_used=token_usage["total_tokens"],
                category=category
            )

        return {
            "content": content,
            "tokens_used": token_usage,
            "model_used": "knowledge-base",
            "category": category,
            "knowledge_base": self._serialize_faq_match(faq_match)
        }

    def _inject_faq_context(self, base_prompt: str, entry: Any) -> str:
        """Embed FAQ data into the system prompt."""

        snippet = [
            "You have access to the following verified SRM knowledge base entry.",
            "Use it to craft a concise, friendly answer and cite the source when relevant.",
            f"Question: {entry.question}",
            f"Answer: {entry.answer}",
        ]

        if entry.source_name or entry.source_url:
            parts = [part for part in [entry.source_name, entry.source_url] if part]
            snippet.append("Source: " + " — ".join(parts))

        return base_prompt + "\n\n" + "\n".join(snippet)

    def _format_faq_answer(self, entry: Any) -> str:
        """Convert a FAQ entry into a conversational response."""

        lines = [entry.answer.strip()]

        source_parts = [part for part in [entry.source_name, entry.source_url] if part]
        if source_parts:
            lines.append("")
            lines.append("Source: " + " — ".join(source_parts))

        return "\n".join(lines)

    def _append_source_to_response(self, response: str, entry: Any) -> str:
        """Add source attribution to an OpenAI-generated response if missing."""

        if entry.source_name or entry.source_url:
            if "Source:" not in response:
                parts = [part for part in [entry.source_name, entry.source_url] if part]
                response = response.rstrip() + "\n\nSource: " + " — ".join(parts)
        return response

    def _serialize_faq_match(self, match: Optional[FaqMatch]) -> Optional[Dict[str, Any]]:
        """Serialize FAQ metadata for API responses."""

        if not match:
            return None

        entry = match.entry
        return {
            "question": entry.question,
            "category": entry.category.value if entry.category else None,
            "score": round(match.score, 2),
            "source_name": entry.source_name,
            "source_url": entry.source_url,
            "tags": entry.tags,
        }
    
    def _categorize_message(self, message: str) -> str:
        """Categorize user message"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["admission", "apply", "entrance", "exam"]):
            return "admissions"
        elif any(word in message_lower for word in ["course", "program", "study", "academic"]):
            return "academics"
        elif any(word in message_lower for word in ["event", "club", "activity", "festival"]):
            return "campus_life"
        elif any(word in message_lower for word in ["placement", "job", "career", "company"]):
            return "placements"
        elif any(word in message_lower for word in ["fee", "cost", "payment", "scholarship"]):
            return "fees"
        elif any(word in message_lower for word in ["hostel", "accommodation", "room", "stay"]):
            return "hostel"
        else:
            return "general"
    
    async def generate_quick_suggestions(self, user: Optional[User] = None) -> List[Dict[str, str]]:
        """Generate quick suggestion buttons based on user context"""
        suggestions = [
            {
                "title": "Admissions Process",
                "description": "About admission requirements and deadlines",
                "icon": "🎓",
                "category": "admissions"
            },
            {
                "title": "Engineering Programs",
                "description": "Explore top engineering courses at SRM",
                "icon": "⚙️",
                "category": "academics"
            },
            {
                "title": "Hostel Facilities",
                "description": "Information about accommodation and fees",
                "icon": "🏠",
                "category": "hostel"
            },
            {
                "title": "Campus Events",
                "description": "Discover clubs, events, and activities",
                "icon": "🎪",
                "category": "campus_life"
            },
            {
                "title": "Placement Statistics",
                "description": "Career opportunities and company visits",
                "icon": "💼",
                "category": "placements"
            },
            {
                "title": "Fee Structure",
                "description": "Tuition fees and scholarship information",
                "icon": "💰",
                "category": "fees"
            }
        ]
        
        # Personalize suggestions based on user profile
        if user and user.campus:
            suggestions.append({
                "title": f"{user.campus} Campus",
                "description": f"Specific information about {user.campus} campus",
                "icon": "📍",
                "category": "campus_specific"
            })
        
        if user and user.focus:
            suggestions.append({
                "title": f"{user.focus} Focus",
                "description": f"Information related to {user.focus}",
                "icon": "🎯",
                "category": "personalized"
            })
        
        return suggestions


# Create singleton instance
ai_service = AIService()
