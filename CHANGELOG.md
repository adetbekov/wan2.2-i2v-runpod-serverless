# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2025-10-05

### Added
- **Enhanced `image_path` parameter**: Now supports URL downloads in addition to local file paths
  - **HTTP/HTTPS URLs**: Automatically downloads images from web URLs
  - **Local file paths**: Supports paths to images in RunPod network volumes
- **Improved `image_base64` parameter**: Now handles Base64 strings with or without data URI prefix
- New `process_image_path()` function in [handler.py](handler.py) to handle URL and local file path inputs
- New `process_image_base64()` function in [handler.py](handler.py) to handle Base64 image inputs

### Changed
- Updated image processing to copy/download all images to ComfyUI's input directory (`/ComfyUI/input`) for proper compatibility
- Converted all Korean comments in [handler.py](handler.py) to English for better code readability
- Updated [README.md](README.md) with enhanced parameter documentation and usage examples
- Updated [README_kr.md](README_kr.md) with Korean documentation for the enhanced parameters
- Images now return only filename (not full path) to ComfyUI's LoadImage node

### Fixed
- **Critical Fix**: Resolved "Invalid image file" error when using Base64 images
  - Images are now saved to ComfyUI's expected input directory
  - Fixed relative path issue that prevented ComfyUI from finding uploaded images
- Removed duplicate import statements for cleaner code

### Technical Details
- Images from URLs are downloaded to `/ComfyUI/input/` with original file extension
- Base64 images are decoded and saved to `/ComfyUI/input/` as JPEG files
- Local file paths are copied to `/ComfyUI/input/` to ensure ComfyUI can access them
- ComfyUI's LoadImage node now receives only the filename (not full path) for compatibility
- Enhanced error handling for image download, decoding, and file access failures

### Usage Guide
The handler now supports two separate parameters for images:

**For URLs or local file paths**:
```json
{
  "input": {
    "image_path": "https://example.com/image.jpg"
  }
}
```

**For Base64 images** (supports both raw Base64 or data URI format):
```json
{
  "input": {
    "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
  }
}
```

**Important**: Use only one parameter (`image_path` OR `image_base64`), not both.
