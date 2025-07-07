import os
from PIL import Image, ImageChops
from PyPDF2 import PdfReader, PdfWriter
import io

def detect_image_dpi(image):
    """Detect DPI from image metadata or use intelligent defaults"""
    # Try to get DPI from image info
    if hasattr(image, 'info') and 'dpi' in image.info:
        dpi_x, dpi_y = image.info['dpi']
        return max(dpi_x, 300)  # Never go below 300 DPI
    
    # Check for common shipping label dimensions at 300 DPI minimum
    width_px, height_px = image.size
    
    # Standard 4x6 label (minimum 1200x1800 pixels at 300 DPI)
    if width_px >= 1200 and height_px >= 1800:
        # Calculate actual DPI based on standard sizes
        if abs(width_px / 4 - 300) < 50:  # Close to 4 inches wide at 300 DPI
            return 300
        elif abs(width_px / 8 - 300) < 50:  # Close to 8 inches wide at 300 DPI
            return 300
    
    # For high resolution images, preserve their quality
    # Never downscale to less than 300 DPI
    estimated_dpi = width_px / 4  # Assume 4 inch width minimum
    return max(estimated_dpi, 300)

def get_size_inches(image):
    """Get image size in inches using detected DPI, maintaining quality"""
    width_px, height_px = image.size
    dpi = detect_image_dpi(image)
    
    # If image is smaller than 4x6 at 300 DPI, we have a problem
    min_width_px = 4 * 300  # 1200 pixels
    min_height_px = 6 * 300  # 1800 pixels
    
    if width_px < min_width_px or height_px < min_height_px:
        print(f"WARNING: Image resolution too low for quality printing. "
              f"Got {width_px}x{height_px}, need at least {min_width_px}x{min_height_px}")
    
    return width_px / dpi, height_px / dpi, dpi

def get_size_inches_legacy(width_px, height_px, dpi=300):
    """Legacy function for backward compatibility"""
    return width_px / dpi, height_px / dpi

def validate_label_quality(image, min_width_in=4, min_height_in=6, min_dpi=300):
    """Validate image meets minimum quality requirements"""
    width_px, height_px = image.size
    width_in, height_in, detected_dpi = get_size_inches(image)
    
    # Check pixel dimensions for minimum DPI at target size
    required_width_px = min_width_in * min_dpi
    required_height_px = min_height_in * min_dpi
    
    if width_px < required_width_px or height_px < required_height_px:
        raise ValueError(
            f"Image resolution too low for quality printing. "
            f"Image is {width_px}x{height_px} pixels ({width_in:.1f}x{height_in:.1f} inches). "
            f"Minimum required: {required_width_px}x{required_height_px} pixels "
            f"for {min_width_in}x{min_height_in} inch label at {min_dpi} DPI."
        )
    
    return True

def save_image_as_pdf_with_exact_size(image, output_filename, width_in=4, height_in=6):
    """Save image as PDF with exact page size in inches"""
    # Get image dimensions
    width_px, height_px = image.size
    
    # Calculate the DPI that would make this image exactly the target size
    # This ensures the PDF page will be exactly width_in x height_in
    dpi_x = width_px / width_in
    dpi_y = height_px / height_in
    
    # Use the smaller DPI to ensure the entire image fits
    # This maintains aspect ratio while ensuring the page is the exact size
    dpi = min(dpi_x, dpi_y)
    
    # Save with calculated DPI
    # The resolution parameter in PIL sets the DPI metadata
    image.save(output_filename, format='PDF', resolution=dpi)
    
    print(f"Saved PDF with DPI: {dpi:.1f} for exact {width_in}\"x{height_in}\" page size")
    return dpi

def resize_pdf_to_exact_dimensions(input_pdf, output_pdf, target_width_in=4, target_height_in=6):
    """Resize PDF pages to exact dimensions in inches - only if they're close to target size"""
    target_width_pts = target_width_in * 72  # 288 pts for 4 inches
    target_height_pts = target_height_in * 72  # 432 pts for 6 inches
    
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    
    for i, page in enumerate(reader.pages):
        # Get current dimensions
        current_width = float(page.mediabox.width)
        current_height = float(page.mediabox.height)
        
        # Check if the page is already close to the target size (within 10%)
        width_ratio = current_width / target_width_pts
        height_ratio = current_height / target_height_pts
        
        # Only resize if the page is within reasonable bounds (0.5x to 1.5x target)
        # This prevents distortion of pages that are significantly different sizes
        if 0.5 <= width_ratio <= 1.5 and 0.5 <= height_ratio <= 1.5:
            # Set the media box to exact target size
            page.mediabox.lower_left = (0, 0)
            page.mediabox.upper_right = (target_width_pts, target_height_pts)
            print(f"Resized page {i+1} from {current_width:.1f}x{current_height:.1f} pts to {target_width_pts}x{target_height_pts} pts")
        else:
            # Keep original size for pages that are too different
            print(f"Kept page {i+1} at original size {current_width:.1f}x{current_height:.1f} pts (too different from target)")
        
        # Add the page
        writer.add_page(page)
    
    with open(output_pdf, 'wb') as f:
        writer.write(f)

def check_aspect_ratio(width, height):
    """Check if aspect ratio is between 65-68%"""
    ratio = (width / height) * 100
    if ratio < 65 or ratio > 68:
        print(f"WRONG RATIO: {ratio:.1f}%")
    return ratio

def combine_pngs_to_pdf(image_files, output_filename, target_width_in=4, target_height_in=6):
    """Combine PNG images into a PDF with exact page dimensions"""
    import tempfile
    import os
    
    if not image_files:
        return 0
    
    # If only one image, save it directly with exact size
    if len(image_files) == 1:
        img = Image.open(image_files[0]).convert('RGB')
        
        # Validate quality
        try:
            validate_label_quality(img)
        except ValueError as e:
            print(f"Warning: {e}")
        
        width_in, height_in, dpi = get_size_inches(img)
        print(f"Image: {width_in:.2f}\" x {height_in:.2f}\" at {dpi} DPI")
        check_aspect_ratio(img.width, img.height)
        
        # Save with exact size
        save_image_as_pdf_with_exact_size(img, output_filename, target_width_in, target_height_in)
        
        # Ensure the PDF has exact dimensions
        temp_output = output_filename + '.temp'
        resize_pdf_to_exact_dimensions(output_filename, temp_output, target_width_in, target_height_in)
        os.replace(temp_output, output_filename)
        
        return 1
    
    # For multiple images, create individual PDFs then combine
    temp_pdfs = []
    temp_dir = tempfile.mkdtemp()
    
    try:
        for i, img_file in enumerate(image_files):
            img = Image.open(img_file).convert('RGB')
            
            # Validate quality
            try:
                validate_label_quality(img)
            except ValueError as e:
                print(f"Warning for image {i+1}: {e}")
            
            width_in, height_in, dpi = get_size_inches(img)
            print(f"Page {i+1} (Image): {width_in:.2f}\" x {height_in:.2f}\" at {dpi} DPI")
            check_aspect_ratio(img.width, img.height)
            
            # Save each image as a PDF with exact size
            temp_pdf = os.path.join(temp_dir, f"page_{i+1}.pdf")
            save_image_as_pdf_with_exact_size(img, temp_pdf, target_width_in, target_height_in)
            temp_pdfs.append(temp_pdf)
        
        # Combine all PDFs
        writer = PdfWriter()
        for pdf_file in temp_pdfs:
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                writer.add_page(page)
        
        # Write combined PDF
        with open(output_filename, 'wb') as f:
            writer.write(f)
        
        # Ensure all pages have exact dimensions
        temp_output = output_filename + '.temp'
        resize_pdf_to_exact_dimensions(output_filename, temp_output, target_width_in, target_height_in)
        os.replace(temp_output, output_filename)
        
        return len(image_files)
        
    finally:
        # Clean up temp files
        for temp_pdf in temp_pdfs:
            try:
                os.remove(temp_pdf)
            except:
                pass
        try:
            os.rmdir(temp_dir)
        except:
            pass

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
            
            print(f"Page {current_page + i + 1} (PDF) dimensions: {width_pt:.1f} x {height_pt:.1f} pts ({width_in:.2f}\" x {height_in:.2f}\")")
            check_aspect_ratio(width_pt, height_pt)  # We can use points directly as ratio will be the same
            
            # Add page without modification to preserve original content
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
        print(f"Output Page {i+1}: {width_pt:.1f} x {height_pt:.1f} pts ({width_in:.2f}\" x {height_in:.2f}\")")
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
        
        # Convert to image with high DPI for quality preservation
        pil_image = convert_from_bytes(page_bytes.getvalue(), dpi=300)[0]
        
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
            
        # Convert back to PDF with high DPI
        pdf_bytes = io.BytesIO()
        final_image.save(pdf_bytes, format='PDF', resolution=300)
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
    
    # Separate image and PDF files
    image_files = [os.path.join(input_dir, f) for f in files 
                   if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    pdf_files = [os.path.join(input_dir, f) for f in files if f.lower().endswith('.pdf')]
    
    total_pages = 0
    
    # Process based on file type
    if image_files and pdf_files:
        # Handle mixed file types: convert images to PDFs first, then combine all
        import tempfile
        temp_pdfs = []
        
        # Convert each image to a temporary PDF
        for img_file in image_files:
            temp_pdf = os.path.join(input_dir, f"temp_{os.path.basename(img_file)}.pdf")
            img = Image.open(img_file).convert('RGB')
            
            # Validate quality
            try:
                validate_label_quality(img)
            except ValueError as e:
                print(f"Warning for {os.path.basename(img_file)}: {e}")
            
            # Print dimensions with detected DPI
            width_in, height_in, dpi = get_size_inches(img)
            print(f"Converting image {os.path.basename(img_file)}: {width_in:.2f}\" x {height_in:.2f}\" at {dpi} DPI")
            check_aspect_ratio(img.width, img.height)
            
            # Save as PDF with exact 4x6 inch size
            save_image_as_pdf_with_exact_size(img, temp_pdf, 4, 6)
            temp_pdfs.append(temp_pdf)
        
        # Combine all PDFs (original + converted images)
        all_pdfs = pdf_files + temp_pdfs
        total_pages = combine_pdfs(all_pdfs, output_filename)
        
        # Clean up temporary PDFs
        for temp_pdf in temp_pdfs:
            try:
                os.remove(temp_pdf)
            except:
                pass
                
        print(f"Combined {len(image_files)} image files and {len(pdf_files)} PDF files into {total_pages} pages")
    elif image_files:
        total_pages = combine_pngs_to_pdf(image_files, output_filename)
        print(f"Created PDF from {len(image_files)} image files with {total_pages} pages")
    elif pdf_files:
        total_pages = combine_pdfs(pdf_files, output_filename)
        print(f"Combined {len(pdf_files)} PDF files with total {total_pages} pages")
    else:
        print("No image (PNG/JPG/JPEG) or PDF files found in the specified directory")
        return total_pages
    
    # Print dimensions of output PDF
    print_output_dimensions(output_filename)
    
    # Only resize if we processed images (not pure PDFs)
    if image_files:
        # Ensure all pages are exactly 4x6 inches for images
        temp_output = output_filename + '.resized'
        resize_pdf_to_exact_dimensions(output_filename, temp_output, 4, 6)
        os.replace(temp_output, output_filename)
        print("\nApplied size corrections where needed")
    else:
        print("\nKeeping original PDF dimensions (no images to resize)")
    
    # Skip trimming if poppler is not installed
    try:
        # Create trimmed version
        output_trimmed = output_filename.replace('.pdf', '_trimmed.pdf')
        trim_pdf_margins(output_filename, output_trimmed)
        
        # Only resize trimmed version if we had images
        if image_files:
            temp_trimmed = output_trimmed + '.resized'
            resize_pdf_to_exact_dimensions(output_trimmed, temp_trimmed, 4, 6)
            os.replace(temp_trimmed, output_trimmed)
    except Exception as e:
        print(f"Skipping PDF trimming: {e}")
        # Continue without trimming
    
    return total_pages

if __name__ == "__main__":
    # Example usage
    input_directory = "./imgs"  # Your input directory
    output_file = "combined_output.pdf"  # Your desired output filename
    
    total_pages = process_files(input_directory, output_file)
