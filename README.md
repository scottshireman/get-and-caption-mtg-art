# get-and-caption-mtg-art
Download all unique art from scryfall and caption it with BLIP2

1. run windows.setup.cmd at command line to setup venv and install dependencies
2. Download the bulk data Unique Art JSON from https://scryfall.com/docs/api/bulk-data and put it in the folder with the scripts
3. run python get_all_cards.py

Wait a long time for the script to download all art and create text tag files for each with card metadata. When its done, continue:

5. run python caption_magic_art.py ==img_dir images
6. delete *.txt files from image folder once all yamnl files have been created.

Result will be all unique art downloaded to image folder with a yaml file for each image with a BLIP2 caption and tags with the cards metadata suitable for fine-tuning with a Stable Diffusion trainer like EveryDream2.

Note #5 requires 24GB VRAM. Alternatively if you have 64GB RAM you can run with --force_cpu, but it will be considerably slow. You can also find other BLIP2 models on HuggingFace that require less VRAM.
