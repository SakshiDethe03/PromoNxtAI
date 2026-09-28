# PromoNxtAI System Architecture

## Overview
PromoNxtAI is an intelligent marketing and promotional platform built with FastAPI, LangGraph multi-agent systems, and a modern frontend interface.

## Components
1. **Backend API (`backend/app/main.py`)**: REST interface for frontend communication.
2. **AI Agents (`backend/app/agents/`)**: Specialized autonomous agents (Content Generator, Strategy Planner, Analytics Evaluator).
3. **Agent Graph (`backend/app/graph/`)**: LangGraph orchestration for multi-agent workflows.
4. **Tools & Services (`backend/app/tools/`, `backend/app/services/`)**: Third-party integrations (social media, email engines, CRM APIs).
