"""Analytics, structured queries, and metrics endpoints."""

from fastapi import APIRouter, Depends

from enterprise_ai.api.dependencies import get_analytics_service
from enterprise_ai.schemas.analytics import AnalyticsSummaryResponse
from enterprise_ai.schemas.common import APIResponse
from enterprise_ai.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=APIResponse[AnalyticsSummaryResponse])
async def get_summary(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> APIResponse[AnalyticsSummaryResponse]:
    """Retrieve platform usage analytics summary."""
    data = await analytics_service.get_system_summary()
    return APIResponse(
        success=True,
        data=AnalyticsSummaryResponse(
            total_documents=data["total_documents"],
            total_chunks=data["total_chunks"],
            system_status=data["system_status"],
        ),
    )

