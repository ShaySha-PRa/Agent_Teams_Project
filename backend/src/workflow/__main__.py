"""Allow running the sample workflow via `python -m src.workflow`."""
from .runner import run_sample_workflow
import asyncio

asyncio.run(run_sample_workflow())
