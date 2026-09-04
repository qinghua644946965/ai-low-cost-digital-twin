"""Extension seam for a future photo/natural-language semantic producer."""

from typing import Any, Protocol


class SpatialSemanticProvider(Protocol):
    def create_scene(self, prompt: str, image_paths: list[str] | None = None) -> dict[str, Any]:
        """Return a scene conforming to examples/scene.schema.json."""
        ...


def from_ai(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
    raise NotImplementedError("Connect an AI provider here; the MVP uses checked-in scene JSON.")
