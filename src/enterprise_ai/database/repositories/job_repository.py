"""Repository for processing jobs and safe job claiming."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai.database.base import ProcessingJob
from enterprise_ai.database.repositories.base_repository import BaseRepository


class JobRepository(BaseRepository[ProcessingJob]):
    """Create, list, claim and update document-processing jobs."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ProcessingJob, session)

    async def create_job(
        self,
        *,
        document_id: uuid.UUID,
        job_type: str,
        status: str = "pending",
        max_attempts: int = 3,
    ) -> ProcessingJob:
        """Create a processing job record."""
        return await self.create(
            document_id=document_id,
            job_type=job_type,
            status=status,
            attempts=0,
            max_attempts=max_attempts,
            error_message=None,
            started_at=None,
            completed_at=None,
            worker_id=None,
            claimed_at=None,
            lease_expires_at=None,
        )

    async def list_pending_jobs(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ProcessingJob]:
        """Return queued jobs that are eligible for processing."""
        result = await self.session.execute(
            select(ProcessingJob)
            .where(ProcessingJob.status.in_(["pending", "queued", "retrying"]))
            .order_by(ProcessingJob.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def claim_next_pending(
        self,
        *,
        worker_id: str,
        lease_seconds: int = 300,
    ) -> ProcessingJob | None:
        """Claim the oldest pending job without blocking on an already-locked row."""
        now = datetime.now(UTC)
        lease_expiry = now + timedelta(seconds=lease_seconds)
        result = await self.session.execute(
            select(ProcessingJob)
            .where(ProcessingJob.status.in_(["pending", "queued", "retrying"]))
            .order_by(ProcessingJob.created_at.asc())
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        job = result.scalar_one_or_none()
        if job is None:
            return None

        job.status = "running"
        job.worker_id = worker_id
        job.claimed_at = now
        job.lease_expires_at = lease_expiry
        job.started_at = now
        job.attempts = (job.attempts or 0) + 1
        await self.session.flush()
        await self.session.refresh(job)
        return job

    async def update_status(
        self,
        job_id: uuid.UUID,
        *,
        status: str,
        error_message: str | None = None,
    ) -> ProcessingJob | None:
        """Transition the job status and optional error message."""
        job = await self.get_by_id(job_id)
        if job is None:
            return None
        job.status = status
        if error_message is not None:
            job.error_message = error_message
        if status in {"completed", "failed"}:
            job.completed_at = datetime.now(UTC)
            job.worker_id = None
            job.claimed_at = None
            job.lease_expires_at = None
        await self.session.flush()
        await self.session.refresh(job)
        return job

    async def mark_completed(self, job_id: uuid.UUID) -> ProcessingJob | None:
        """Mark a job as complete and release the lease."""
        job = await self.get_by_id(job_id)
        if job is None:
            return None
        job.status = "completed"
        job.completed_at = datetime.now(UTC)
        job.worker_id = None
        job.claimed_at = None
        job.lease_expires_at = None
        await self.session.flush()
        await self.session.refresh(job)
        return job

    async def mark_failed(
        self,
        job_id: uuid.UUID,
        *,
        error_message: str,
        max_attempts: int | None = None,
    ) -> ProcessingJob | None:
        """Mark a job as failed, optionally scheduling a retry."""
        job = await self.get_by_id(job_id)
        if job is None:
            return None
        job.error_message = error_message
        job.completed_at = datetime.now(UTC)
        job.worker_id = None
        job.claimed_at = None
        job.lease_expires_at = None
        if max_attempts is not None:
            job.max_attempts = max_attempts
        if job.attempts >= job.max_attempts:
            job.status = "failed"
        else:
            job.status = "retrying"
        await self.session.flush()
        await self.session.refresh(job)
        return job

    async def list_by_document(
        self,
        *,
        document_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ProcessingJob]:
        """Return processing jobs associated with a document."""
        result = await self.session.execute(
            select(ProcessingJob)
            .where(ProcessingJob.document_id == document_id)
            .order_by(ProcessingJob.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
