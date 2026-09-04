from app.models.inference import InferenceProvider
from app.services.mock_provider import MockInferenceProvider
from app.services.pytorch_provider import PyTorchInferenceProvider

class InferenceService:
    """
    Factory & Manager for active InferenceProvider.
    Automatically checks for PyTorch model weights or selects Mock provider.
    """

    def __init__(self):
        self._pytorch_provider = PyTorchInferenceProvider()
        self._mock_provider = MockInferenceProvider()

    def get_provider(self) -> InferenceProvider:
        if self._pytorch_provider.is_weights_available():
            return self._pytorch_provider
        return self._mock_provider

inference_service_instance = InferenceService()

def get_active_inference_provider() -> InferenceProvider:
    return inference_service_instance.get_provider()
