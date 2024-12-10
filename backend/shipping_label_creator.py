import os
from PIL import Image, ImageChops
from PyPDF2 import PdfReader, PdfWriter
import io

def get_size_inches(width_px, height_px, dpi=96):
    """Convert pixels to inches based on DPI"""
    return width_px / dpi, height_px / dpi

def check_aspect_ratio(width, height):
    """Check if aspect ratio is between 65-68%"""
    ratio = (width / height) * 100
    if ratio < 65 or ratio > 68:
        print(f"WRONG RATIO: {ratio:.1f}%")
    return ratio

def combine_pngs_to_pdf(png_files, output_filename):
    # Open the first image and convert it to RGB mode
    images = [Image.open(png).convert('RGB') for png in png_files]
    
    # Print dimensions for each PNG
    for i, img in enumerate(images):
        width_px, height_px = img.size
        width_in, height_in = get_size_inches(width_px, height_px)
        print(f"Page {i+1} (PNG) dimensions: {width_in:.2f}\" x {height_in:.2f}\"")
        check_aspect_ratio(width_px, height_px)
    
    # Save the first image as a PDF and append the rest
    # Set DPI to 96 to match the input assumption
    images[0].save(output_filename, 
                  save_all=True, 
                  append_images=images[1:],
                  resolution=96.0)  # This sets the DPI for the PDF output
    
    return len(images)

def combine_pdfs(pdf_files, output_filename):
    writer = PdfWriter()
    total_pages = 0
    
    for pdf_file in pdf_files:
        reader = PdfReader(pdf_file)
        current_page = total_pages
        
        for i, page in enumerate(reader.pages):
            # Get page dimensions in points (1/72 of an inch)
            width_pt = float(page.mediabox.width)
            height_pt = float(page.mediabox.height)
            
            # Convert to inches (1 point = 1/72 inch)
            width_in = width_pt / 72
            height_in = height_pt / 72
            
            print(f"Page {current_page + i + 1} (PDF) dimensions: {width_in:.2f}\" x {height_in:.2f}\"")
            check_aspect_ratio(width_pt, height_pt)  # We can use points directly as ratio will be the same
            
            writer.add_page(page)
        
        total_pages += len(reader.pages)
    
    # Write the combined PDF to the output file
    with open(output_filename, 'wb') as output_file:
        writer.write(output_file)
    
    return total_pages

def print_output_dimensions(output_filename):
    """Print dimensions of each page in the output PDF"""
    print("\nOutput PDF dimensions:")
    reader = PdfReader(output_filename)
    for i, page in enumerate(reader.pages):
        width_pt = float(page.mediabox.width)
        height_pt = float(page.mediabox.height)
        width_in = width_pt / 72
        height_in = height_pt / 72
        print(f"Output Page {i+1} dimensions: {width_in:.2f}\" x {height_in:.2f}\"")
        check_aspect_ratio(width_pt, height_pt)

def add_padding_for_ratio(image, target_ratio=66.7):
    """Add padding to image to maintain target ratio (width/height * 100)"""
    width, height = image.size
    current_ratio = (width / height) * 100
    
    # If ratio is already between 65-68%, keep original dimensions
    if 65 <= current_ratio <= 68:
        return image
    
    # Create new white background
    if current_ratio > target_ratio:
        # Need to add height
        new_height = int(width * 100 / target_ratio)
        new_width = width
    else:
        # Need to add width
        new_width = int(height * target_ratio / 100)
        new_height = height
    
    new_image = Image.new('RGB', (new_width, new_height), 'white')
    
    # Center the original image
    paste_x = (new_width - width) // 2
    paste_y = (new_height - height) // 2
    new_image.paste(image, (paste_x, paste_y))
    
    return new_image

def trim_pdf_margins(input_pdf, output_pdf):
    """Create a new PDF with trimmed margins and 66.7% ratio"""
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    
    print("\nTrimmed Output PDF dimensions:")
    for i, page in enumerate(reader.pages):
        # Convert PDF page to PIL Image for trimming
        from pdf2image import convert_from_bytes
        
        # Convert PDF page to bytes
        temp_writer = PdfWriter()
        temp_writer.add_page(page)
        page_bytes = io.BytesIO()
        temp_writer.write(page_bytes)
        page_bytes.seek(0)
        
        # Convert to image with specific DPI to match original size
        original_width_pt = float(page.mediabox.width)
        target_width_px = int(original_width_pt * 96 / 72)  # Convert from points to pixels at 96 DPI
        dpi = int(target_width_px * 72 / original_width_pt)  # Calculate required DPI
        
        pil_image = convert_from_bytes(page_bytes.getvalue(), dpi=dpi)[0]
        
        # Trim white margins
        bg = Image.new(pil_image.mode, pil_image.size, 'white')
        diff = ImageChops.difference(pil_image, bg)
        bbox = diff.getbbox()
        if bbox:
            trimmed_image = pil_image.crop(bbox)
        else:
            trimmed_image = pil_image
        
        # Add padding to maintain 66.7% ratio
        final_image = add_padding_for_ratio(trimmed_image, 66.7)
            
        # Convert back to PDF with correct DPI
        pdf_bytes = io.BytesIO()
        final_image.save(pdf_bytes, format='PDF', resolution=dpi)
        pdf_bytes.seek(0)
        
        # Add to writer
        temp_reader = PdfReader(pdf_bytes)
        writer.add_page(temp_reader.pages[0])
        
        # Print dimensions
        width_in = float(temp_reader.pages[0].mediabox.width) / 72
        height_in = float(temp_reader.pages[0].mediabox.height) / 72
        ratio = (width_in / height_in) * 100
        print(f"Trimmed Page {i+1} dimensions: {width_in:.2f}\" x {height_in:.2f}\" (ratio: {ratio:.1f}%)")
    
    # Save the trimmed PDF
    with open(output_pdf, 'wb') as output_file:
        writer.write(output_file)

def process_files(input_dir, output_filename):
    # Get all files in the input directory
    files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
    
    # Separate PNG and PDF files
    png_files = [os.path.join(input_dir, f) for f in files if f.lower().endswith('.png')]
    pdf_files = [os.path.join(input_dir, f) for f in files if f.lower().endswith('.pdf')]
    
    total_pages = 0
    
    # Process based on file type
    if png_files:
        total_pages = combine_pngs_to_pdf(png_files, output_filename)
        print(f"Created PDF from {len(png_files)} PNG files with {total_pages} pages")
    elif pdf_files:
        total_pages = combine_pdfs(pdf_files, output_filename)
        print(f"Combined {len(pdf_files)} PDF files with total {total_pages} pages")
    else:
        print("No PNG or PDF files found in the specified directory")
        return total_pages
    
    # Print dimensions of output PDF
    print_output_dimensions(output_filename)
    
    # Create trimmed version
    output_trimmed = output_filename.replace('.pdf', '_trimmed.pdf')
    trim_pdf_margins(output_filename, output_trimmed)
    
    return total_pages

if __name__ == "__main__":
    # Example usage
    input_directory = "./imgs"  # Your input directory
    output_file = "combined_output.pdf"  # Your desired output filename
    
    total_pages = process_files(input_directory, output_file)
