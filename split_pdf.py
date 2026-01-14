import fitz
import math
import logging

logging.basicConfig(level=logging.INFO)

# ============== CONSTANTS ==============
A4_WIDTH = 595    # Points (72 DPI)
A4_HEIGHT = 842   # Points (72 DPI)


# ============== CORE LOGIC ==============
def calculate_slices(page_width, page_height, overlap_mm):
    """
    Calculate how many A4 pages needed to cover the source page.
    
    Args:
        page_width: Source page width in points
        page_height: Source page height in points
        overlap_mm: Overlap amount in millimeters
    
    Returns:
        (num_slices, scale_factor, overlap_in_points)
    """
    scale = A4_WIDTH / page_width
    overlap_pt = overlap_mm * 72 / 25.4  # Convert mm to points
    
    # How much vertical space each A4 page covers (minus overlap)
    slice_height = (A4_HEIGHT - overlap_pt) / scale
    
    # How many slices needed
    num_slices = math.ceil((page_height - overlap_pt) / slice_height)
    
    return num_slices, scale, overlap_pt


def split_pdf(
    output_path,
    input_path,
    overlap=8,
    dpi=300,
    progress_callback=None,
    cancel_check=None
):
    """
    Split a PDF into multiple A4 pages with optional overlap.
    
    Args:
        output_path: Path to save output PDF
        input_path: Path to source PDF
        overlap: Overlap in millimeters (default 8)
        dpi: DPI for rendering (72-600, default 300)
        progress_callback: Function(percent, status_msg) for progress updates
        cancel_check: Function() -> bool to check if cancellation requested
    
    Returns:
        True if successful, False if cancelled or failed
    """
    doc = None
    out = None
    
    try:
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
            page_width, page_height, overlap
        )
        
        # Calculate actual slice height
        slice_height = (A4_HEIGHT - overlap_pt) / scale
        
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
            
            # Create new A4 page
            new_page = out.new_page(width=A4_WIDTH, height=A4_HEIGHT)
            
            # Define clip region from source
            clip = fitz.Rect(0, y0, page_width, y1)
            
            # Calculate scaled height (actual content height)
            clip_height = clip.height
            target_height = clip_height * scale
            
            # Place content at TOP of page (not centered)
            target_rect = fitz.Rect(0, 0, A4_WIDTH, target_height)
            
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
