from flask import Flask, request, send_file, render_template, after_this_request, jsonify
from split_pdf import split_pdf
import os
import fitz
import threading
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ============== THREAD-SAFE STATE ==============
state_lock = threading.Lock()
conversion_lock = threading.Lock()  # Prevent concurrent conversions

state = {
    "percent": 0,
    "status": "Idle",
    "error": None,
    "cancel_requested": False,
    "is_converting": False,  # Single source of truth for conversion state
    "output_size": None,
    "output_pages": None
}

TEMP_DIR = "."
INPUT_FILE = os.path.join(TEMP_DIR, "input.pdf")
OUTPUT_FILE = os.path.join(TEMP_DIR, "output.pdf")


# ============== HELPERS ==============
def is_pdf_file(filename):
    """Validate that uploaded file is a PDF."""
    return filename.lower().endswith(".pdf")


def cleanup_files():
    """Safely remove temporary files."""
    for f in [INPUT_FILE, OUTPUT_FILE]:
        try:
            if os.path.exists(f):
                os.remove(f)
        except Exception as e:
            logging.warning(f"Failed to remove {f}: {e}")


def set_state(percent=None, status=None, error=None):
    """Thread-safe state update."""
    with state_lock:
        if percent is not None:
            state["percent"] = percent
        if status is not None:
            state["status"] = status
        if error is not None:
            state["error"] = error


def get_state():
    """Thread-safe state read."""
    with state_lock:
        return dict(state)


def should_cancel():
    """Thread-safe cancel check."""
    with state_lock:
        return state["cancel_requested"]


# ============== ROUTES ==============
@app.route("/")
def home():
    return render_template("home.html")


@app.route("/pdf-to-a4")
def pdf_to_a4():
    return render_template("index.html")


@app.route("/progress")
def get_progress():
    """Return current progress."""
    return jsonify(get_state())


@app.route("/cancel", methods=["POST"])
def cancel():
    """Request conversion cancellation."""
    with state_lock:
        state["cancel_requested"] = True
        state["status"] = "Cancelling..."
    
    # Release lock immediately so next conversion can start
    # Lock will be released again in worker thread finally block (harmless)
    conversion_lock.release()
    
    return {"status": "ok"}


@app.route("/estimate", methods=["POST"])
def estimate():
    """Estimate pages and file size (metadata only - no conversion)."""
    try:
        # Validate PDF file
        pdf_file = request.files.get("pdf")
        if not pdf_file or not is_pdf_file(pdf_file.filename):
            return {"error": "Invalid PDF file"}, 400

        overlap = float(request.form.get("overlap", 8))
        dpi = int(request.form.get("dpi", 300))
        paper_format = request.form.get("paper_format", "A4")

        # Validate parameters
        if overlap < 0 or overlap > 50 or dpi < 72 or dpi > 600:
            return {"error": "Invalid overlap or DPI"}, 400
            
        # Validate paper format (basic check, split_pdf handles detailed check)
        valid_formats = ["A2", "A3", "A4", "A5", "Letter"]
        if paper_format not in valid_formats:
            return {"error": "Invalid paper format"}, 400

        # Save temp file to get metadata
        temp_file = os.path.join(TEMP_DIR, "temp_estimate.pdf")
        pdf_file.save(temp_file)

        try:
            # Open PDF and get page info
            doc = fitz.open(temp_file)
            page_count = doc.page_count
            file_size = os.path.getsize(temp_file) / (1024 * 1024)
            doc.close()

            return jsonify({"pages": page_count, "size": f"{round(file_size, 2)} MB"})

        finally:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass

    except Exception as e:
        logging.error(f"Estimate failed: {e}")
        return {"error": str(e)}, 500


@app.route("/upload", methods=["POST"])
def upload():
    """Start conversion in background thread."""
    try:
        # Prevent concurrent conversions
        if not conversion_lock.acquire(blocking=False):
            logging.warning("Attempted to start conversion while one is already running")
            return {"error": "A conversion is already in progress. Please wait for it to complete or cancel it."}, 429

        # Validate PDF file
        pdf_file = request.files.get("pdf")
        if not pdf_file or not is_pdf_file(pdf_file.filename):
            conversion_lock.release()
            return {"error": "Invalid PDF file"}, 400

        overlap = float(request.form.get("overlap", 8))
        dpi = int(request.form.get("dpi", 300))
        paper_format = request.form.get("paper_format", "A4")

        # Validate parameters
        if overlap < 0 or dpi < 72 or dpi > 600:
            conversion_lock.release()
            return {"error": "Invalid overlap or DPI"}, 400
            
        valid_formats = ["A2", "A3", "A4", "A5", "Letter"]
        if paper_format not in valid_formats:
            conversion_lock.release()
            return {"error": "Invalid paper format"}, 400

        # Reset state and save file
        with state_lock:
            # Clear all previous state
            state["percent"] = 0
            state["status"] = "Starting..."
            state["error"] = None
            state["cancel_requested"] = False
            state["output_size"] = None
            state["output_pages"] = None
            state["is_converting"] = True  # Mark conversion as active

        cleanup_files()
        pdf_file.save(INPUT_FILE)

        # Start worker thread
        thread = threading.Thread(
            target=run_conversion,
            args=(overlap, dpi, paper_format),
            daemon=False
        )
        thread.start()

        return {"status": "started"}

    except Exception as e:
        logging.error(f"Upload failed: {e}")
        conversion_lock.release()
        return {"error": str(e)}, 500


@app.route("/download")
def download():
    """Download converted PDF and cleanup."""
    try:
        if not os.path.exists(OUTPUT_FILE):
            return {"error": "File not ready"}, 404

        @after_this_request
        def cleanup(response):
            cleanup_files()
            with state_lock:
                state["output_size"] = None
                state["output_pages"] = None
            set_state(percent=0, status="Idle", error=None)
            return response

        return send_file(OUTPUT_FILE, as_attachment=True, download_name="output.pdf")

    except Exception as e:
        logging.error(f"Download failed: {e}")
        return {"error": str(e)}, 500


# ============== WORKER THREAD ==============
def run_conversion(overlap, dpi, paper_format):
    """Background worker - runs in thread."""
    try:
        if not os.path.exists(INPUT_FILE):
            set_state(status="Error: Input file missing", error="File not found")
            return

        def progress_cb(percent, status_msg):
            """Called by split_pdf to update progress."""
            set_state(percent=percent, status=status_msg)

        # Run conversion
        success = split_pdf(
            OUTPUT_FILE,
            INPUT_FILE,
            overlap=overlap,
            dpi=dpi,
            paper_format=paper_format,
            progress_callback=progress_cb,
            cancel_check=should_cancel
        )

        with state_lock:
            if state["cancel_requested"]:
                state["status"] = "Cancelled"
                state["percent"] = 0
                state["output_size"] = None
                state["output_pages"] = None
            elif success:
                # Get output file size and page count
                if os.path.exists(OUTPUT_FILE):
                    output_size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
                    state["output_size"] = f"{round(output_size_mb, 2)} MB"
                    
                    # Get output page count
                    try:
                        out_doc = fitz.open(OUTPUT_FILE)
                        state["output_pages"] = out_doc.page_count
                        out_doc.close()
                    except:
                        state["output_pages"] = None
                        
                state["status"] = "Ready for download"
                state["percent"] = 100
            else:
                state["status"] = "Error: Processing failed"
                state["error"] = "Conversion completed with errors"
                state["output_size"] = None
                state["output_pages"] = None

    except Exception as e:
        logging.error(f"Conversion failed: {e}")
        set_state(status="Error", error=str(e))

    finally:
        with state_lock:
            state["is_converting"] = False  # Mark conversion as complete
        conversion_lock.release()  # Release lock after conversion completes


# ============== RUN ================
if __name__ == "__main__":
    import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
