"""Servicio orquestador de negocio multimedia."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from clibaseapp import BrowseResult, scan_files
from data.repository import MediaRepository
from models.schemas import (
    ActionType,
    AuditSummary,
    CleanPlan,
    MediaFile,
    OptimizationProfile,
    OptimizeFailure,
    OptimizeOutcome,
    OptimizePlan,
    OptimizeResult,
)
from services.audit_service import AuditService
from services.clean_service import CleanService
from services.optimize_service import DEFAULT_OPTIMIZATION_PROFILES, OptimizeService

VIDEO_EXTENSIONS = {".mkv", ".mp4", ".m4v"}


@dataclass
class CleanFailure:
    file_path: Path
    message: str


@dataclass
class CleanResult:
    files_processed: int
    files_with_errors: int
    bytes_saved: int
    failures: List[CleanFailure] = field(default_factory=list)


class MediaService:
    """Servicio principal que orquesta auditoria, limpieza y optimizacion."""

    def __init__(self) -> None:
        self.repo = MediaRepository()
        self.audit_service = AuditService()
        self.clean_service = CleanService()
        self.optimize_service = OptimizeService()

    def list_optimization_profiles(self):
        return self.optimize_service.list_profiles()

    def build_custom_optimization_recommendations(self, media_files: List[MediaFile]):
        """Expone recomendaciones guiadas sin acoplar la UI al servicio interno."""
        return self.optimize_service.build_custom_recommendations(media_files)

    def _resolve_files(self, result: BrowseResult) -> List[Path]:
        if result.selection_type == "file":
            return [result.selected_path]
        return scan_files(result.selected_path, VIDEO_EXTENSIONS)

    def audit(self, result: Optional[BrowseResult]) -> AuditSummary:
        if result is None:
            return AuditSummary(
                cancelled=True,
                selected_path=None,
                selection_type=None,
                scanned_files=0,
                report=None,
            )

        files = self._resolve_files(result)
        if not files:
            return AuditSummary(
                cancelled=False,
                selected_path=result.selected_path,
                selection_type=result.selection_type,
                scanned_files=0,
                report=None,
            )

        analyzed = self.repo.analyze_many(files)
        report = self.audit_service.build_report(analyzed)
        return AuditSummary(
            cancelled=False,
            selected_path=result.selected_path,
            selection_type=result.selection_type,
            scanned_files=len(files),
            report=report,
        )

    def build_clean_plans(self, result: BrowseResult, keep_languages: List[str]) -> List[CleanPlan]:
        files = self._resolve_files(result)
        if not files:
            return []

        analyzed = self.repo.analyze_many(files)
        return self.build_clean_plans_from_media_files(analyzed, keep_languages)

    def build_clean_plans_from_media_files(
        self,
        media_files: List[MediaFile],
        keep_languages: List[str],
    ) -> List[CleanPlan]:
        if not media_files:
            return []

        return [self.clean_service.build_plan(media_file, keep_languages) for media_file in media_files]

    def execute_clean_plan(self, plan: CleanPlan) -> int:
        to_remove = [action for action in plan.track_actions if action.action == ActionType.REMOVE]
        if not to_remove:
            return 0

        initial_size = plan.media_file.path.stat().st_size
        self.repo.execute_remux(plan)
        final_size = plan.media_file.path.stat().st_size
        return max(0, initial_size - final_size)

    def execute_clean_plans(self, plans: List[CleanPlan]) -> CleanResult:
        total_saved = 0
        failures: List[CleanFailure] = []

        for plan in plans:
            try:
                total_saved += self.execute_clean_plan(plan)
            except Exception as exc:
                failures.append(CleanFailure(file_path=plan.media_file.path, message=str(exc)))

        return CleanResult(
            files_processed=len(plans),
            files_with_errors=len(failures),
            bytes_saved=total_saved,
            failures=failures,
        )

    def build_optimize_plans_from_media_files(
        self,
        media_files: List[MediaFile],
        profile: OptimizationProfile | None = None,
        profile_id: str = DEFAULT_OPTIMIZATION_PROFILES[0].id,
    ) -> List[OptimizePlan]:
        if not media_files:
            return []

        selected_profile = profile or self.optimize_service.get_profile(profile_id)
        return self.optimize_service.build_plans(media_files, selected_profile)

    def execute_optimize_plan(self, plan: OptimizePlan) -> OptimizeOutcome:
        return self.repo.execute_optimization(plan)

    def execute_optimize_plans(self, plans: List[OptimizePlan]) -> OptimizeResult:
        outputs: List[OptimizeOutcome] = []
        skipped: List[OptimizePlan] = []
        failures: List[OptimizeFailure] = []

        for plan in plans:
            if not plan.can_optimize:
                skipped.append(plan)
                continue
            try:
                outputs.append(self.execute_optimize_plan(plan))
            except Exception as exc:
                failures.append(OptimizeFailure(file_path=plan.media_file.path, message=str(exc)))

        return OptimizeResult(
            files_processed=len(plans),
            files_optimized=len(outputs),
            files_skipped=len(skipped),
            files_with_errors=len(failures),
            bytes_saved=sum(output.bytes_saved for output in outputs),
            outputs=outputs,
            skipped=skipped,
            failures=failures,
        )

    def replace_originals_with_optimized(self, outputs: List[OptimizeOutcome]) -> List[OptimizeFailure]:
        failures: List[OptimizeFailure] = []
        for output in outputs:
            try:
                self.repo.replace_original_with_output(output)
            except Exception as exc:
                failures.append(OptimizeFailure(file_path=output.input_path, message=str(exc)))
        return failures
