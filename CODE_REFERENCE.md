# PDF to A4 UI Refactoring - Code Reference

## 1. Processing Modal HTML Structure

```html
<!-- PROCESSING MODAL -->
<div id="processingModal" class="modal-overlay">
    <div class="modal-card">
        <div class="spinner"></div>
        <div class="modal-title">Processing your request</div>
        <div class="modal-subtitle">Please wait while we process your request. Do not refresh the page.</div>
        <button type="button" id="modalCancelBtn" class="modal-button" onclick="cancelJob()">Cancel</button>
    </div>
</div>
```

## 2. Overlap Counter Control HTML

```html
<div class="form-group">
    <label>Overlap (mm)</label>
    <div class="overlap-control">
        <button type="button" id="overlapMinus" class="overlap-btn" onclick="decreaseOverlap()">−</button>
        <div class="overlap-value" id="overlapValue">8</div>
        <button type="button" id="overlapPlus" class="overlap-btn" onclick="increaseOverlap()">+</button>
    </div>
</div>
```

## 3. DPI Slider HTML

```html
<div class="form-group">
    <div class="slider-group">
        <div class="slider-label-row">
            <label>DPI</label>
            <div class="dpi-value" id="dpiValue">DPI: 300</div>
        </div>
        <input type="range" id="dpi" min="150" max="600" value="300" step="1" oninput="updateDpiLabel()">
    </div>
</div>
```

## 4. Modal CSS - Overlay

```css
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.3);
    display: none;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    animation: fadeIn 0.2s ease;
}

.modal-overlay.show {
    display: flex;
}
```

## 5. Modal CSS - Card

```css
.modal-card {
    background: #fff;
    border-radius: 16px;
    padding: 40px 32px;
    max-width: 420px;
    width: 90%;
    text-align: center;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
    animation: slideUp 0.3s ease;
}

body.dark .modal-card {
    background: #1a1a1a;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}
```

## 6. Spinner Animation CSS

```css
.spinner {
    width: 48px;
    height: 48px;
    border: 4px solid #e5e5e5;
    border-top-color: #000;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 24px;
}

body.dark .spinner {
    border-color: #2a2a2a;
    border-top-color: #fff;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}
```

## 7. Animation Keyframes

```css
@keyframes fadeIn {
    from {
        opacity: 0;
    }
    to {
        opacity: 1;
    }
}

@keyframes slideUp {
    from {
        transform: translateY(20px);
        opacity: 0;
    }
    to {
        transform: translateY(0);
        opacity: 1;
    }
}
```

## 8. Overlap Control CSS

```css
.overlap-control {
    display: flex;
    gap: 8px;
    background: #f5f5f5;
    border-radius: 12px;
    padding: 2px;
    align-items: center;
    justify-content: center;
}

body.dark .overlap-control {
    background: #222;
}

.overlap-btn {
    width: 44px;
    height: 44px;
    border: none;
    background: transparent;
    font-size: 20px;
    cursor: pointer;
    border-radius: 8px;
    transition: all 0.2s ease;
    font-weight: 600;
}

.overlap-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}

.overlap-btn:hover:not(:disabled) {
    background: #e0e0e0;
}

body.dark .overlap-btn:hover:not(:disabled) {
    background: #333;
}

.overlap-value {
    min-width: 60px;
    text-align: center;
    font-weight: 600;
    font-size: 16px;
}
```

## 9. DPI Slider CSS

```css
input[type="range"] {
    width: 100%;
    height: 6px;
    border-radius: 3px;
    background: #e5e5e5;
    outline: none;
    -webkit-appearance: none;
}

body.dark input[type="range"] {
    background: #2a2a2a;
}

input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #000;
    cursor: pointer;
    transition: all 0.2s ease;
}

body.dark input[type="range"]::-webkit-slider-thumb {
    background: #fff;
}

input[type="range"]::-webkit-slider-thumb:hover {
    transform: scale(1.2);
}

input[type="range"]::-moz-range-thumb {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #000;
    cursor: pointer;
    border: none;
    transition: all 0.2s ease;
}

body.dark input[type="range"]::-moz-range-thumb {
    background: #fff;
}
```

## 10. JavaScript - Overlap Counter Functions

```javascript
function decreaseOverlap() {
    if (overlapVal > 0) {
        overlapVal--;
        overlapValue.innerText = overlapVal;
        updateOverlapButtons();
    }
}

function increaseOverlap() {
    if (overlapVal < 30) {
        overlapVal++;
        overlapValue.innerText = overlapVal;
        updateOverlapButtons();
    }
}

function updateOverlapButtons() {
    overlapMinus.disabled = overlapVal <= 0;
    overlapPlus.disabled = overlapVal >= 30;
}
```

## 11. JavaScript - DPI Slider Function

```javascript
function updateDpiLabel() {
    dpiVal = parseInt(dpiSlider.value);
    dpiValueDisplay.innerText = `DPI: ${dpiVal}`;
}
```

## 12. JavaScript - Modal Control Functions

```javascript
function showModal() {
    processingModal.classList.add("show");
}

function hideModal() {
    processingModal.classList.remove("show");
}
```

## 13. JavaScript - Global Variables

```javascript
let pollTimer = null;
let estimateData = null;
let isEstimating = false;
let isProcessing = false;
let isSubmitting = false;
let overlapVal = 8;
let dpiVal = 300;
```

## 14. JavaScript - Form Submit Handler (Key Parts)

```javascript
form.addEventListener("submit", async (e) => {
    e.preventDefault();
    
    const overlap = overlapVal;
    const dpi = dpiVal;
    
    // Validation...
    if (overlap < 0 || overlap > 30) {
        updateCard("Validation Error", "Overlap must be between 0-30 mm", "", true);
        return;
    }
    
    if (dpi < 150 || dpi > 600) {
        updateCard("Validation Error", "DPI must be between 150-600", "", true);
        return;
    }
    
    // Show modal
    showModal();
    updateCard("Processing…", "Starting conversion");
    
    // Upload and poll...
});
```

## 15. JavaScript - Progress Polling (Key Changes)

```javascript
function pollProgress() {
    pollTimer = setInterval(async () => {
        const state = await res.json();
        
        // Handle completion - hide modal
        if (state.percent >= 100) {
            clearInterval(pollTimer);
            hideModal();  // ← KEY: Hide modal on completion
            downloadBtn.disabled = false;
            updateCard("Download Ready", "Conversion complete", ...);
        }
        
        // Handle cancellation - hide modal
        if (state.status === "Cancelled") {
            clearInterval(pollTimer);
            hideModal();  // ← KEY: Hide modal on cancel
            submitBtn.disabled = false;
            updateCard("Conversion cancelled", "Ready to convert again", ...);
        }
    }, 500);
}
```

## 16. JavaScript - Cancel Handler

```javascript
function cancelJob() {
    fetch("/cancel", { method: "POST" })
        .then(() => {
            if (pollTimer) clearInterval(pollTimer);
            hideModal();  // ← Close modal
            submitBtn.disabled = false;
            isProcessing = false;
            isSubmitting = false;
            downloadBtn.disabled = true;
            updateCard(
                "Conversion cancelled",
                "Ready to convert again",
                estimateData ? `Input: ${estimateData.pages} pages | ${estimateData.size}` : ""
            );
        })
        .catch(err => {
            console.error("Cancel error:", err);
            hideModal();
        });
}
```

## 17. JavaScript - Reset Handler

```javascript
function reset() {
    form.reset();
    errorDiv.classList.remove("show");
    downloadBtn.disabled = true;
    submitBtn.disabled = false;
    estimateData = null;
    isProcessing = false;
    isSubmitting = false;
    
    // Reset overlap counter
    overlapVal = 8;
    overlapValue.innerText = overlapVal;
    updateOverlapButtons();
    
    // Reset DPI slider
    dpiSlider.value = 300;
    dpiVal = 300;
    updateDpiLabel();
    
    updateCard("Ready to convert", "Upload a PDF to begin");
}
```

## 18. Initialization

```javascript
// Initialize overlap buttons state on page load
updateOverlapButtons();
```

## Key Design Patterns

### Modal Activation/Deactivation
- **Activate**: `showModal()` → adds "show" class → CSS displays flex
- **Deactivate**: `hideModal()` → removes "show" class → CSS displays none
- **Trigger**: Form submit → `showModal()` shows modal during processing
- **Auto-hide**: Poll completion → `hideModal()` closes modal

### Overlap Counter State Management
- **Global State**: `overlapVal` (0-30, default 8)
- **UI Sync**: `overlapValue.innerText = overlapVal`
- **Button State**: Minus/Plus disabled at boundaries via `updateOverlapButtons()`
- **Form Data**: Uses `overlapVal` directly, not form input

### DPI Slider State Management
- **Global State**: `dpiVal` (150-600, default 300)
- **Live Update**: `oninput="updateDpiLabel()"` triggers on slider move
- **Display Update**: `dpiValueDisplay.innerText = 'DPI: ' + dpiVal`
- **Form Data**: Uses `dpiVal` directly, not form input

### Error Handling
- **Modal Close**: Always call `hideModal()` on error before showing error message
- **State Cleanup**: Set `isProcessing = false`, `isSubmitting = false` on error
- **Button State**: Re-enable `submitBtn`, disable `downloadBtn` on error
