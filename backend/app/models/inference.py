from abc import ABC, abstractmethod
from typing import Dict, Any, List
from app.schemas.detection import ImageAnalysisResult, SSLFeatures

class InferenceProvider(ABC):
    """
    Abstract Inference Interface for SonarAI.
    Both MockInferenceProvider and PyTorchInferenceProvider implement this interface.
    The Frontend & Analysis Service must interact ONLY with this interface.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns provider label e.g. 'MockInferenceProvider' or 'PyTorchInferenceProvider'"""
        pass

    @property
    @abstractmethod
    def is_mock(self) -> bool:
        """Indicates if inference is DEMO/MOCK or real PyTorch model"""
        pass

    @abstractmethod
    def load_model(self) -> bool:
        """Initialize or check model weights"""
        pass

    @abstractmethod
    def predict(
        self,
        image_path: str,
        output_dir: str,
        image_id: str,
        filename: str,
        image_index: int,
        latitude: float | None = None,
        longitude: float | None = None,
        location_note: str = "Location data unavailable"
    ) -> ImageAnalysisResult:
        """
        Runs complete SSS inference pipeline on a single image file:
        1. SSL Feature extraction
        2. Segmentation & Object detection (Shipwreck vs Unknown)
        3. Confidence & Novelty score calculation
        4. Output image generation (segmentation mask PNG, overlay PNG, thumbnail JPG)
        Returns structured ImageAnalysisResult.
        """
        pass
