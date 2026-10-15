import numpy as np
import torch

def clip_similarity_to_probs(similarities, threshold: float = 0.25, scale: int = 40) -> torch.Tensor:
    if isinstance(similarities, torch.Tensor):
        return torch.sigmoid(scale * (similarities - threshold))
    elif isinstance(similarities, (float, np.ndarray)):
        x = scale * (similarities - threshold)
        return 1 / (1 + np.exp(-x))
    else:
        raise TypeError(f"Tipo no soportado: {type(similarities)}")