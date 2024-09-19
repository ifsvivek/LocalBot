import os
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'

import torch
from diffusers import FluxPipeline

def flux(prompt):
    pipe = FluxPipeline.from_pretrained("black-forest-labs/FLUX.1-dev", torch_dtype=torch.bfloat16)
    pipe.enable_model_cpu_offload()

    image = pipe(
        prompt=prompt,
        height=512,
        width=512,
        guidance_scale=3.5,
        num_inference_steps=30,
        max_sequence_length=512,
        generator=torch.Generator("cpu").manual_seed(0)
    ).images[0]
    image.save("img/flux-dev.png")

if __name__ == "__main__":
    import sys
    prompt = sys.argv[1]
    flux(prompt)