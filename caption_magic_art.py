"""
Copyright [2022-2023] Scott Shireman

Licensed under the GNU Affero General Public License;
You may not use this code except in compliance with the License.
You may obtain a copy of the License at

    https://www.gnu.org/licenses/agpl-3.0.en.html

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os

from PIL import Image
import argparse
import requests
from transformers import Blip2Processor, Blip2ForConditionalGeneration

import torch
from  pynvml import *

import time
from colorama import Fore, Style
from clip_interrogator import Config, Interrogator, LabelTable, load_list
from unidecode import unidecode


SUPPORTED_EXT = [".jpg", ".png", ".jpeg", ".bmp", ".jfif", ".webp"]

def get_args(**parser_kwargs):
    """Get command-line options."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--img_dir",
        type=str,
        default="output",
        help="Path to input images. (default: 'output')"
        )
    parser.add_argument(
        "--blip_model",
        type=str,
        default="salesforce/blip2-opt-6.7b",
        help="BLIP2 moodel from huggingface. (default: salesforce/blip2-opt-6.7b)"
        )

    parser.add_argument(
        "--force_cpu",
        action="store_true",
        default=False,
        help="Force using CPU for BLIP even if GPU is available. You need at least 24GB VRAM to use GPU and 64GB to use CPU but it will likely be very slow. I have not tested this."
        )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite an existing YAML. Otherwise if a YAML file exists it just skips it."
        )


    args = parser.parse_args()

    return args

def get_gpu_memory_map():
    """Get the current gpu usage.
    Returns
    -------
    usage: dict
        Keys are device ids as integers.
        Values are memory usage as integers in MB.
    """
    nvmlInit()
    handle = nvmlDeviceGetHandleByIndex(0)
    info = nvmlDeviceGetMemoryInfo(handle)
    return info.used/1024/1024

def create_blip2_processor(model_name, device, dtype=torch.float16):
    processor = Blip2Processor.from_pretrained( model_name )
    model = Blip2ForConditionalGeneration.from_pretrained( model_name, torch_dtype=dtype )
    model.to(device)
    model.eval()
    print(f"BLIP2 Model loaded: {model_name}")
    return processor, model

def query_blip (full_file_path, blip_processor, blip_model, device, dtype, args):

    full_tags_path = os.path.splitext(full_file_path)[0] + '.txt'
    yaml_caption_path = os.path.splitext(full_file_path)[0] + '.yaml'

    if not os.path.exists(yaml_caption_path) or args.overwrite:

        with open(full_tags_path, 'r') as f:
           caption_tags = f.read()

        f.close()
            
        image = Image.open(full_file_path)

        #query BLIP
        inputs = blip_processor(images=image, return_tensors="pt").to(device, dtype)

        text_caption = []

        print(full_file_path)
        start_time = time.time()

        generated_ids = blip_model.generate(**inputs, max_new_tokens=24)
        blip_caption = blip_processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()

        full_txt_caption = ", ".join([blip_caption, caption_tags])

        process_time = round(time.time() - start_time,2)
        print(f"Caption generated in {process_time} sec.: {full_txt_caption}")

        write_yaml_file(yaml_caption_path, blip_caption, caption_tags)

    else: 
        print(f"\t Skipping {full_file_path} because yaml caption already exists.")
                                 

    
def write_yaml_file(yaml_file_path, blip_caption, delimitted_tags, delimitter = ','):

    yaml_caption = "main_prompt: " + blip_caption + "\ntags:"

    for caption_tag in delimitted_tags.split(delimitter):
        if caption_tag.strip() != "":
            yaml_caption = yaml_caption + "\n  - tag: " + caption_tag.strip()

    with open(yaml_file_path, "w") as f:
        f.write(yaml_caption)

def main():

    args = get_args()
    print(f"** Captioning files in: {args.img_dir}")
    
    start_time = time.time()
    files_processed = 0

    device = "cuda" if torch.cuda.is_available() and not args.force_cpu else "cpu"
    dtype = torch.float32 if args.force_cpu else torch.float16

    #Open BLIP2 model
    start_blip_load = time.time()
    print(f"Loading BLIP2 model {args.blip_model} . . .")
    blip_processor, blip_model = create_blip2_processor(args.blip_model, device, dtype)
    print(f"Loaded BLIP2 model in {time.time() - start_blip_load} seconds.")
    print(f"GPU memory used: {get_gpu_memory_map()} MB")


    if os.path.isfile(args.img_dir):
        query_blip(args.img_dir, blip_processor, blip_model, device, dtype)

    else:
        # os.walk all files in args.img_dir recursively
        for root, dirs, files in os.walk(args.img_dir):
            for file in files:
                #get file extension
                ext = os.path.splitext(file)[1]
                if ext.lower() in SUPPORTED_EXT:
                    query_blip(os.path.join(root, file), blip_processor, blip_model, device, dtype, args)
                    files_processed = files_processed + 1

    exec_time = time.time() - start_time
    print(f"  Processed {files_processed} files in {exec_time} seconds for an average of {exec_time/files_processed} sec/file.")
    

if __name__ == "__main__":

    main()
