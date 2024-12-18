import torch
from petals.constants import PUBLIC_INITIAL_PEERS

from data_structures import ModelBackendConfig, ModelChatConfig, ModelConfig, ModelFrontendConfig

default_chat_config = ModelChatConfig(
    max_session_length=8192,
    sep_token="###",
    stop_token="###",
    extra_stop_sequences=["</s>"],
    generation_params=dict(do_sample=1, temperature=0.6, top_p=0.9),
)

MODEL_FAMILIES = {
    "BLOOM": [
        ModelConfig(
            ModelBackendConfig(repository="bigscience/bloom-560m"),
            ModelFrontendConfig(
                name="BLOOM-560m",
                model_card="https://huggingface.co/bigscience/bloom-560m",
                license="https://bit.ly/bloom-license",
            ),
            ModelChatConfig(
                max_session_length=2048,
                sep_token="\n\n",
                stop_token="</s>",
                extra_stop_sequences=["\n\nHuman"],
                generation_params=default_chat_config.generation_params,
            ),
        ),
    ],
}

INITIAL_PEERS = ['/ip4/3.88.87.174/tcp/31337/p2p/Qmc6dHz9W4gTmQRkCBSvhQjgeZ9cmEakhSpcDCaoy9YSA5']

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

try:
    from cpufeature import CPUFeature

    has_avx512 = CPUFeature["AVX512f"] and CPUFeature["OS_AVX512"]
except ImportError:
    has_avx512 = False

if DEVICE == "cuda":
    TORCH_DTYPE = "auto"
elif has_avx512:
    TORCH_DTYPE = torch.bfloat16
else:
    TORCH_DTYPE = torch.float32
STEP_TIMEOUT = 5 * 60
