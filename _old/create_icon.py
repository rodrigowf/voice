from PIL import Image, ImageDraw

def create_icon(size=256, color='green'):
    # Create a new image with a black background
    image = Image.new('RGB', (size, size), color='black')
    draw = ImageDraw.Draw(image)
    
    # Draw a circle with the specified color
    margin = size // 8
    draw.ellipse([margin, margin, size - margin, size - margin], fill=color)
    
    # Save the icon
    image.save('icon.png')

if __name__ == '__main__':
    create_icon() 