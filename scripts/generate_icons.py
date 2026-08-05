from PIL import Image, ImageDraw


def create_icon(path: str, size: int) -> None:
    # Create a transparent image
    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # Draw a blue circle
    margin = size // 10
    draw.ellipse((margin, margin, size - margin, size - margin), fill=(52, 152, 219))

    # Draw a generic water drop shape using polygon and ellipse
    drop_width = size // 4
    drop_height = size // 3
    center_x = size // 2
    center_y = size // 2 + size // 10

    # Base circle of the drop
    draw.ellipse((center_x - drop_width, center_y - drop_width,
                  center_x + drop_width, center_y + drop_width), fill=(255, 255, 255))

    # Top triangle of the drop
    draw.polygon([
        (center_x, center_y - drop_height),
        (center_x - drop_width, center_y),
        (center_x + drop_width, center_y)
    ], fill=(255, 255, 255))

    img.save(path)

create_icon('custom_components/ecowater_cloud/icon.png', 512)
create_icon('custom_components/ecowater_cloud/logo.png', 512)
print("Icons generated!")
