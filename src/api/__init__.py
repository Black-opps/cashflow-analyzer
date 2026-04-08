"""
API routes for cashflow analyzer.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from uuid import UUID

from ..services.analyzer import CashflowAnalyzer
from ..services.report_generator import ReportGenerator
from ..core.config import settings

# Import the router from routes.py
from .routes import router

# Re-export the router
__all__ = ["router"]