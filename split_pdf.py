import fitz
import math
import logging

logging.basicConfig(level=logging.INFO)

# ============== CONSTANTS ==============
# Dimensions in points (72 DPI)
PAPER_FORMATS = {
    "A2": {"width": 1191, "height": 1684},
    "A3": {"width": 842, "height": 1191},
    "A4": {"width": 595, "height": 842},
    "A5": {"width": 420, "height": 595},
    "Letter": {"width": 612, "height": 792}
}


# ============== CORE LOGIC ==============
def calculate_slices(page_width, page_height, overlap_mm, target_width, target_height):
    """
    Calculate how many target pages needed to cover the source page.
    
    Args:
        page_width: Source page width in points
        page_height: Source page height in points
        overlap_mm: Overlap amount in millimeters
        target_width: Target page width in points
        target_height: Target page height in points
    
    Returns:
        (num_slices, scale_factor, overlap_in_points)
    """
    scale = target_width / page_width
    overlap_pt = overlap_mm * 72 / 25.4  # Convert mm to points
    
    # How much vertical space each target page covers (minus overlap)
    slice_height = (target_height - overlap_pt) / scale
    
    # How many slices needed
    num_slices = math.ceil((page_height - overlap_pt) / slice_height)
    
    return num_slices, scale, overlap_pt


def split_pdf(
    output_path,
    input_path,
    overlap=8,
    dpi=300,
    paper_format="A4",
    progress_callback=None,
    cancel_check=None
):
    """
    Split a PDF into multiple pages of specified format with optional overlap.
    
    Args:
        output_path: Path to save output PDF
        input_path: Path to source PDF
        overlap: Overlap in millimeters (default 8)
        dpi: DPI for rendering (72-600, default 300)
        paper_format: Target paper format (default "A4")
        progress_callback: Function(percent, status_msg) for progress updates
        cancel_check: Function() -> bool to check if cancellation requested
    
    Returns:
        True if successful, False if cancelled or failed
    """
    doc = None
    out = None
    
    try:
        # Get target dimensions
        if paper_format not in PAPER_FORMATS:
            logging.warning(f"Unknown paper format {paper_format}, defaulting to A4")
            paper_format = "A4"
            
        target_dims = PAPER_FORMATS[paper_format]
        target_w = target_dims["width"]
        target_h = target_dims["height"]
        
        # Open source document
        doc = fitz.open(input_path)
        if doc.page_count == 0:
            logging.error("Source PDF has no pages")
            return False
        
        src_page = doc[0]
        page_width = src_page.rect.width
        page_height = src_page.rect.height
        
        # Calculate slicing parameters
        num_slices, scale, overlap_pt = calculate_slices(
            page_width, page_height, overlap, target_w, target_h
        )
        
        # Calculate actual slice height
        slice_height = (target_h - overlap_pt) / scale
        
        # Create output document
        out = fitz.open()
        
        # Process each slice
        for i in range(num_slices):
            
            # Check for cancellation
            if cancel_check and cancel_check():
                logging.info("Conversion cancelled by user")
                return False
            
            # Update progress
            if progress_callback:
                percent = int((i / num_slices) * 90)  # Leave 10% for saving
                progress_callback(percent, f"Processing page {i+1}/{num_slices}")
            
            # Calculate Y coordinates for this slice
            y0 = max(0, i * slice_height - overlap_pt / scale)
            y1 = min(y0 + slice_height + overlap_pt / scale, page_height)
            
            # Create new page
            new_page = out.new_page(width=target_w, height=target_h)
            
            # Define clip region from source
            clip = fitz.Rect(0, y0, page_width, y1)
            
            # Calculate scaled height (actual content height)
            clip_height = clip.height
            target_height = clip_height * scale
            
            # Place content at TOP of page (not centered)
            target_rect = fitz.Rect(0, 0, target_w, target_height)
            
            # Render clipped portion onto new page
            new_page.show_pdf_page(
                target_rect,
                doc,
                0,
                clip=clip
            )
        
        # Save output
        if progress_callback:
            progress_callback(95, "Saving PDF...")
        
        out.save(output_path)
        
        if progress_callback:
            progress_callback(100, "Completed")
        
        logging.info(f"Successfully created {num_slices} pages at {output_path}")
        return True
        
    except Exception as e:
        logging.error(f"PDF splitting failed: {e}")
        return False
    
    finally:
        # Ensure documents are closed
        if doc:
            doc.close()
        if out:
            out.close()
