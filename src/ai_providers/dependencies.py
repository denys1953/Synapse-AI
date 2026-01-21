from functools import lru_cache
from typing import Annotated

from .vector_store import VectorService

from fastapi import Depends

@lru_cache()
def get_vector_service() -> VectorService:
    return VectorService()

VectorServiceDep = Annotated[VectorService, Depends(get_vector_service)]
