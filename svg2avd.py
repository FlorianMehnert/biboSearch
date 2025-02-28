#!/usr/bin/env python3
"""
Inkscape SVG to Android Vector Drawable Converter

This script converts Inkscape SVG files to Android Vector Drawable (AVD) format.
It handles various SVG elements and attributes, mapping them to the corresponding
Android Vector Drawable XML format.
"""

import os
import sys
import re
import argparse
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Define XML namespaces
SVG_NS = "{http://www.w3.org/2000/svg}"
INKSCAPE_NS = "{http://www.inkscape.org/namespaces/inkscape}"
ANDROID_NS = "http://schemas.android.com/apk/res/android"


def register_namespaces():
    """Register XML namespaces for proper parsing"""
    ET.register_namespace('', "http://www.w3.org/2000/svg")
    ET.register_namespace('android', ANDROID_NS)
    ET.register_namespace('inkscape', "http://www.inkscape.org/namespaces/inkscape")


def parse_transform(transform_str):
    """Parse SVG transform attribute to extract matrix values"""
    if not transform_str:
        return None

    matrix_match = re.search(r'matrix\((.*?)\)', transform_str)
    if matrix_match:
        values = [float(v.strip()) for v in matrix_match.group(1).split(',')]
        return values

    # Handle translate, scale, etc. if needed
    return None


def convert_color(color):
    """Convert SVG color to Android color format"""
    if not color:
        return None

    # Handle transparent/none
    if color.lower() in ['none', 'transparent']:
        return '@android:color/transparent'

    # Convert hex colors
    if color.startswith('#'):
        if len(color) == 4:  # #RGB format
            r, g, b = color[1], color[2], color[3]
            return f'#{r}{r}{g}{g}{b}{b}'
        return color

    # Handle named colors (could be expanded)
    color_map = {
        'black': '#000000',
        'white': '#FFFFFF',
        'red': '#FF0000',
        'green': '#00FF00',
        'blue': '#0000FF',
    }
    return color_map.get(color.lower(), color)


def create_path_from_element(element):
    """Create a vector path element from an SVG element"""
    path = ET.Element("path")

    # Handle different SVG elements
    tag_name = element.tag.replace(SVG_NS, '')

    if tag_name == 'path':
        path.set("android:pathData", element.get('d', ''))

    elif tag_name == 'rect':
        x = float(element.get('x', '0'))
        y = float(element.get('y', '0'))
        width = float(element.get('width', '0'))
        height = float(element.get('height', '0'))
        rx = element.get('rx')
        ry = element.get('ry')

        if rx is not None and ry is None:
            ry = rx
        elif ry is not None and rx is None:
            rx = ry

        if rx is not None and ry is not None and float(rx) > 0 and float(ry) > 0:
            # Rounded rectangle
            rx, ry = float(rx), float(ry)
            path_data = f"M {x + rx},{y} h {width - 2 * rx} a {rx},{ry} 0 0 1 {rx},{ry} v {height - 2 * ry} a {rx},{ry} 0 0 1 {-rx},{ry} h {-(width - 2 * rx)} a {rx},{ry} 0 0 1 {-rx},{-ry} v {-(height - 2 * ry)} a {rx},{ry} 0 0 1 {rx},{-ry} z"
        else:
            # Regular rectangle
            path_data = f"M {x},{y} h {width} v {height} h {-width} z"

        path.set("android:pathData", path_data)

    elif tag_name == 'circle':
        cx = float(element.get('cx', '0'))
        cy = float(element.get('cy', '0'))
        r = float(element.get('r', '0'))
        # Approximation of a circle using 4 cubic bezier curves
        path_data = f"M {cx},{cy - r} a {r},{r} 0 0 1 0,{2 * r} a {r},{r} 0 0 1 0,{-2 * r} z"
        path.set("android:pathData", path_data)

    elif tag_name == 'ellipse':
        cx = float(element.get('cx', '0'))
        cy = float(element.get('cy', '0'))
        rx = float(element.get('rx', '0'))
        ry = float(element.get('ry', '0'))
        path_data = f"M {cx},{cy - ry} a {rx},{ry} 0 0 1 0,{2 * ry} a {rx},{ry} 0 0 1 0,{-2 * ry} z"
        path.set("android:pathData", path_data)

    elif tag_name == 'line':
        x1 = float(element.get('x1', '0'))
        y1 = float(element.get('y1', '0'))
        x2 = float(element.get('x2', '0'))
        y2 = float(element.get('y2', '0'))
        path_data = f"M {x1},{y1} L {x2},{y2}"
        path.set("android:pathData", path_data)

    elif tag_name == 'polyline':
        points = element.get('points', '')
        if points:
            point_pairs = points.strip().replace(',', ' ').split()
            point_pairs = [point_pairs[i:i + 2] for i in range(0, len(point_pairs), 2)]
            if point_pairs:
                path_data = f"M {','.join(point_pairs[0])}"
                for pair in point_pairs[1:]:
                    path_data += f" L {','.join(pair)}"
                path.set("android:pathData", path_data)

    elif tag_name == 'polygon':
        points = element.get('points', '')
        if points:
            point_pairs = points.strip().replace(',', ' ').split()
            point_pairs = [point_pairs[i:i + 2] for i in range(0, len(point_pairs), 2)]
            if point_pairs:
                path_data = f"M {','.join(point_pairs[0])}"
                for pair in point_pairs[1:]:
                    path_data += f" L {','.join(pair)}"
                path_data += " Z"
                path.set("android:pathData", path_data)

    # Handle common style attributes
    fill = None
    stroke = None
    stroke_width = None

    # Parse style attribute if present
    style = element.get('style')
    if style:
        # Extract fill, stroke, stroke-width from style attribute
        fill_match = re.search(r'fill:(.*?)(;|$)', style)
        if fill_match:
            fill = fill_match.group(1).strip()

        stroke_match = re.search(r'stroke:(.*?)(;|$)', style)
        if stroke_match:
            stroke = stroke_match.group(1).strip()

        stroke_width_match = re.search(r'stroke-width:(.*?)(;|$)', style)
        if stroke_width_match:
            stroke_width = stroke_width_match.group(1).strip()

    # Direct attributes override style attributes
    fill = element.get('fill', fill)
    stroke = element.get('stroke', stroke)
    stroke_width = element.get('stroke-width', stroke_width)

    # Set Android attributes
    if fill and fill.lower() != 'none':
        path.set("android:fillColor", convert_color(fill))
    else:
        path.set("android:fillColor", "@android:color/transparent")

    if stroke and stroke.lower() != 'none':
        path.set("android:strokeColor", convert_color(stroke))
        if stroke_width:
            try:
                path.set("android:strokeWidth", str(float(stroke_width)))
            except ValueError:
                # Handle non-numeric stroke-width values
                path.set("android:strokeWidth", "1")
        else:
            path.set("android:strokeWidth", "1")

    # Handle opacity
    opacity = element.get('opacity')
    fill_opacity = element.get('fill-opacity')
    stroke_opacity = element.get('stroke-opacity')

    if opacity:
        try:
            path.set("android:fillAlpha", str(float(opacity)))
            if stroke:
                path.set("android:strokeAlpha", str(float(opacity)))
        except ValueError:
            pass

    if fill_opacity and fill:
        try:
            path.set("android:fillAlpha", str(float(fill_opacity)))
        except ValueError:
            pass

    if stroke_opacity and stroke:
        try:
            path.set("android:strokeAlpha", str(float(stroke_opacity)))
        except ValueError:
            pass

    # Handle transform
    transform = element.get('transform')
    if transform:
        # In a full implementation, you'd handle the transform
        # Converting SVG transforms to Android is complex and would
        # require matrix operations
        pass

    return path


def convert_svg_to_avd(svg_file, output_file=None, width=24, height=24):
    """Convert an SVG file to Android Vector Drawable format"""
    if not output_file:
        base_name = os.path.splitext(svg_file)[0]
        output_file = f"{base_name}.xml"

    register_namespaces()

    try:
        tree = ET.parse(svg_file)
        svg_root = tree.getroot()
    except Exception as e:
        print(f"Error parsing SVG file: {e}")
        return False

    # Create Android Vector Drawable
    vector = ET.Element("vector")
    vector.set("xmlns:android", ANDROID_NS)

    # Get viewBox from SVG
    viewbox = svg_root.get('viewBox')
    if viewbox:
        vb_parts = [float(p.strip()) for p in viewbox.split()]
        if len(vb_parts) == 4:
            vb_width = vb_parts[2]
            vb_height = vb_parts[3]

            # Set width, height and viewportWidth, viewportHeight
            vector.set("android:width", f"{width}dp")
            vector.set("android:height", f"{height}dp")
            vector.set("android:viewportWidth", str(vb_width))
            vector.set("android:viewportHeight", str(vb_height))
    else:
        # No viewBox, use width and height from SVG
        svg_width = svg_root.get('width', '24')
        svg_height = svg_root.get('height', '24')

        # Remove 'px', 'pt', etc.
        svg_width = re.sub(r'[a-z]+$', '', svg_width)
        svg_height = re.sub(r'[a-z]+$', '', svg_height)

        try:
            vb_width = float(svg_width)
            vb_height = float(svg_height)

            vector.set("android:width", f"{width}dp")
            vector.set("android:height", f"{height}dp")
            vector.set("android:viewportWidth", str(vb_width))
            vector.set("android:viewportHeight", str(vb_height))
        except ValueError:
            # Default values
            vector.set("android:width", f"{width}dp")
            vector.set("android:height", f"{height}dp")
            vector.set("android:viewportWidth", "24")
            vector.set("android:viewportHeight", "24")

    # Process all drawable elements (recursively if needed)
    drawable_tags = [
        f"{SVG_NS}path", f"{SVG_NS}rect", f"{SVG_NS}circle",
        f"{SVG_NS}ellipse", f"{SVG_NS}line", f"{SVG_NS}polyline",
        f"{SVG_NS}polygon"
    ]

    def process_element(element, parent_group=None):
        if element.tag == f"{SVG_NS}g":
            # Process a group element
            group = ET.Element("group")

            # Handle group transform
            transform = element.get('transform')
            if transform:
                # Parse and apply transform (simplified)
                matrix = parse_transform(transform)
                if matrix and len(matrix) == 6:
                    # Apply matrix transformation (a,b,c,d,e,f)
                    # In Android, this would be:
                    # scaleX = a
                    # skewY = b
                    # skewX = c
                    # scaleY = d
                    # translateX = e
                    # translateY = f
                    group.set("android:scaleX", str(matrix[0]))
                    group.set("android:scaleY", str(matrix[3]))
                    group.set("android:translateX", str(matrix[4]))
                    group.set("android:translateY", str(matrix[5]))

            # Add group to parent
            if parent_group is not None:
                parent_group.append(group)
            else:
                vector.append(group)

            # Process children
            for child in element:
                process_element(child, group)

        elif any(element.tag == tag for tag in drawable_tags):
            # Process drawable element
            path = create_path_from_element(element)

            if parent_group is not None:
                parent_group.append(path)
            else:
                vector.append(path)

    # Process all children of the SVG root
    for child in svg_root:
        process_element(child)

    # Write to file with proper formatting
    xml_str = ET.tostring(vector, encoding='unicode')
    pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="    ")

    # Remove XML declaration line
    pretty_xml = '\n'.join(pretty_xml.split('\n')[1:])

    with open(output_file, 'w') as f:
        f.write(pretty_xml)

    print(f"Converted {svg_file} to {output_file}")
    return True


def main():
    parser = argparse.ArgumentParser(description='Convert Inkscape SVG to Android Vector Drawable')
    parser.add_argument('input', help='Input SVG file or directory')
    parser.add_argument('-o', '--output', help='Output AVD file or directory')
    parser.add_argument('-w', '--width', type=int, default=24, help='Vector width in dp (default: 24)')
    parser.add_argument('-h2', '--height', type=int, default=24, help='Vector height in dp (default: 24)')
    parser.add_argument('-r', '--recursive', action='store_true', help='Process directories recursively')

    args = parser.parse_args()

    if os.path.isfile(args.input):
        # Convert single file
        convert_svg_to_avd(args.input, args.output, args.width, args.height)
    elif os.path.isdir(args.input):
        # Process directory
        if args.output and not os.path.isdir(args.output):
            os.makedirs(args.output, exist_ok=True)

        for root, dirs, files in os.walk(args.input):
            for file in files:
                if file.lower().endswith('.svg'):
                    input_file = os.path.join(root, file)

                    if args.output:
                        # Create relative path structure
                        rel_path = os.path.relpath(root, args.input)
                        output_dir = os.path.join(args.output, rel_path)
                        os.makedirs(output_dir, exist_ok=True)

                        base_name = os.path.splitext(file)[0]
                        output_file = os.path.join(output_dir, f"{base_name}.xml")
                    else:
                        output_file = None

                    convert_svg_to_avd(input_file, output_file, args.width, args.height)

            if not args.recursive:
                break
    else:
        print(f"Error: {args.input} is not a valid file or directory")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
