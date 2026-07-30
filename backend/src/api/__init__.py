"""
API v1 Router — aggregates all endpoint groups.

Re-exports the master router from api.router for main.py compatibility.
"""

from api.router import api_v1_router as router
