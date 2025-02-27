import json
import os
import cairosvg
from PIL import Image


def generate_icons(config_file, svg_path, base_name="beeboSearch", output_dir="beeboSearch/icons"):
    """
    Generate PNG icons from an SVG file based on configuration file specifications
    and create monochrome versions for Toga/Briefcase apps.

    Args:
        config_file (str): Path to the SVG to PNG configuration JSON file
        svg_path (str): Path to the source SVG icon
        base_name (str): Base name for the icons
        output_dir (str): Directory where icons will be saved
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    # Load configuration
    with open(config_file, 'r') as f:
        config = json.load(f)

    # Process each icon specification in the configuration
    for file_spec in config.get("files", []):
        name_suffix = file_spec.get("nameSuffix", "")
        width = file_spec.get("width", 32)
        height = file_spec.get("height", 32)

        # Generate colored icon
        icon_name = f"{base_name}{name_suffix}"
        colored_icon_path = os.path.join(output_dir, f"{icon_name}.png")

        # Convert SVG to PNG with specified dimensions
        cairosvg.svg2png(
            url=svg_path,
            write_to=colored_icon_path,
            output_width=width,
            output_height=height
        )
        print(f"Generated colored icon: {colored_icon_path} ({width}x{height})")

        # Generate monochrome version for Toga/Briefcase
        mono_icon_path = os.path.join(output_dir, f"{icon_name}-mono.png")
        generate_monochrome_version(colored_icon_path, mono_icon_path)
        print(f"Generated monochrome icon: {mono_icon_path} ({width}x{height})")


def generate_monochrome_version(source_path, output_path):
    """
    Create a monochrome version of an icon

    Args:
        source_path (str): Path to the colored icon
        output_path (str): Path where the monochrome icon will be saved
    """
    # Open the source image
    with Image.open(source_path) as img:
        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Extract the alpha channel to preserve transparency
        r, g, b, alpha = img.split()

        # Create a grayscale representation of the icon
        gray = Image.new('L', img.size, 0)
        mask = Image.new('L', img.size, 0)

        # For each pixel in the image
        for x in range(img.width):
            for y in range(img.height):
                r_val, g_val, b_val, a_val = img.getpixel((x, y))

                # If pixel is not transparent
                if a_val > 0:
                    # Set to black (0)
                    gray.putpixel((x, y), 0)
                    # Use original alpha as mask
                    mask.putpixel((x, y), a_val)

        # Create a new black image with the original alpha channel
        monochrome = Image.new('RGBA', img.size, (0, 0, 0, 0))
        for x in range(img.width):
            for y in range(img.height):
                if mask.getpixel((x, y)) > 0:
                    monochrome.putpixel((x, y), (0, 0, 0, mask.getpixel((x, y))))

        # Save the monochrome version
        monochrome.save(output_path)


if __name__ == "__main__":
    # You'll need to specify the path to your SVG file
    svg_path = "beeboSearch/icons/beeboSearch_mono.svg"
    generate_icons("svg2pngConfig.json", svg_path)
    print("All icons generated successfully!")
