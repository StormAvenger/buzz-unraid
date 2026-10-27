# SPDX-License-Identifier: MIT
"""Verify real CUDA work. Add --transcribe /input/sample.wav for an inference test."""
import argparse
import os
from pathlib import Path
import sys

# A Docker console does not inherit variables exported only by /startapp.sh.
# Restart once with library paths in place, before importing CUDA libraries.
if os.environ.get("BUZZ_GPU_CHECK_LOADER_READY") != "1":
    import glob
    libraries = sorted(glob.glob("/opt/venv/lib/python3.12/site-packages/nvidia/*/lib"))
    libraries.append("/opt/venv/lib/python3.12/site-packages/torch/lib")
    previous = os.environ.get("LD_LIBRARY_PATH")
    if previous:
        libraries.append(previous)
    os.environ["LD_LIBRARY_PATH"] = ":".join(libraries)
    os.environ["BUZZ_GPU_CHECK_LOADER_READY"] = "1"
    os.execv(sys.executable, [sys.executable, __file__, *sys.argv[1:]])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transcribe", type=Path)
    parser.add_argument("--model", default="tiny", help="Model ID or existing local model folder")
    args = parser.parse_args()
    import torch
    import ctranslate2

    print(f"PyTorch: {torch.__version__}; packaged CUDA: {torch.version.cuda}")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable. Check the Unraid NVIDIA driver and container GPU selection.")
    print(f"GPU: {torch.cuda.get_device_name(0)}; capability: {torch.cuda.get_device_capability(0)}")
    print(f"Compiled architectures: {torch.cuda.get_arch_list()}")
    # This catches 'no kernel image' even when is_available() returns True.
    a = torch.ones((128, 128), device="cuda", dtype=torch.float32)
    result = a @ a
    torch.cuda.synchronize()
    if result[0, 0].item() != 128:
        raise RuntimeError("CUDA computation returned an unexpected result")
    supported = ctranslate2.get_supported_compute_types("cuda", 0)
    print(f"CTranslate2 GPU compute types: {sorted(supported)}")
    if "int8_float32" not in supported:
        raise RuntimeError("The required Pascal-compatible int8_float32 computation is unavailable")
    print("PASS: CUDA computation and CTranslate2 capability checks")
    if args.transcribe:
        if not args.transcribe.is_file():
            raise FileNotFoundError(args.transcribe)
        from faster_whisper import WhisperModel
        model = WhisperModel(
            args.model, device="cuda", device_index=0, compute_type="int8_float32",
            download_root=os.environ.get("BUZZ_MODEL_ROOT", "/config/cache/buzz/models"),
        )
        segments, info = model.transcribe(str(args.transcribe), beam_size=1)
        count = 0
        for segment in segments:
            print(f"{segment.start:.2f}–{segment.end:.2f}: {segment.text}")
            count += 1
        if count == 0:
            raise RuntimeError("No speech segments returned; use a clearly spoken test recording")
        print(f"PASS: Faster Whisper CUDA inference ({count} segments; language {info.language})")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
