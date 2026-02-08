"""Composite extraction provider for mixed OCR/statement backends."""

from app.pkgs.extraction.providers.base import ExtractionPipeline, ExtractionProvider


class CompositeExtractionProvider:
    """Compose independent OCR and statement providers into one pipeline provider."""

    def __init__(
        self,
        *,
        ocr_provider: ExtractionProvider,
        statement_provider: ExtractionProvider,
    ) -> None:
        self.ocr_provider = ocr_provider
        self.statement_provider = statement_provider
        self.name = f"ocr={ocr_provider.name};statement={statement_provider.name}"
        self.ocr_models = ocr_provider.ocr_models
        self.statement_models = statement_provider.statement_models
        self.pipelines = self._build_pipelines()

    def _build_pipelines(self) -> list[ExtractionPipeline]:
        count = min(len(self.ocr_models), len(self.statement_models))
        pipelines = [
            ExtractionPipeline(
                ocr_model=self.ocr_models[idx],
                statement_model=self.statement_models[idx],
            )
            for idx in range(count)
        ]
        if not pipelines:
            raise ValueError("Composite provider has no OCR->statement model pipelines")
        return pipelines

    async def run_ocr(
        self,
        *,
        model: str,
        prompt: str,
        pdf_bytes: bytes,
    ) -> str:
        return await self.ocr_provider.run_ocr(
            model=model,
            prompt=prompt,
            pdf_bytes=pdf_bytes,
        )

    async def run_statement(
        self,
        *,
        model: str,
        prompt: str,
    ) -> str:
        return await self.statement_provider.run_statement(
            model=model,
            prompt=prompt,
        )
