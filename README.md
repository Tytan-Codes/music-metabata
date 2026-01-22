# Classical Music Metadata Tagger

A powerful, AI-driven tool designed to organize, tag, and manage your classical music collection. This script uses the OpenRouter API (Accessing models like Google Gemini, GPT-4, etc.) to intelligently analyze filenames and contexts, generating accurate and standardized metadata for your FLAC files.

## Features

-   **AI-Powered Metadata Tagging**: automatically extracts Composer, Work, Movement, Performers, and more from filenames using advanced LLMs.
-   **Intelligent Renaming**: Renames files to a clean, searchable format (e.g., `Track - Composer - Work - Movement - Performer`).
-   **Format Conversion**: Automatically converts non-FLAC audio files (MP3, M4A, WAV, etc.) to FLAC using `ffmpeg`.
-   **Metadata Audit & Repair**: Scans your entire library to verify consistency, identify missing tags, and suggest improvements.
-   **Cover Art Generation**: Generates unique, minimalist, and "luxurious" cover art for tracks missing artwork.
-   **Library Statistics**: meaningful insights into your collection, including metadata coverage, top composers, and missing fields.
-   **Interactive TUI**: A beautiful terminal user interface built with `rich` for easy navigation.

## Prerequisites

Before running the script, ensure you have the following installed:

1.  **Python 3.8+**
2.  **FFmpeg**: Required for audio conversion.
    ```bash
    brew install ffmpeg  # macOS (Homebrew)
    sudo apt install ffmpeg  # Ubuntu/Debian
    ```
3.  **OpenRouter API Key**: You need an API key from [OpenRouter](https://openrouter.ai/) to power the AI tagging.

## Installation

1.  Clone this repository or download the `music.py` script.
2.  Install the required Python dependencies:

    ```bash
    pip install mutagen openai rich pillow
    ```

## Configuration

Set your OpenRouter API key as an environment variable:

```bash
export OPENROUTER_API_KEY="your-api-key-here"
```

You can add this line to your shell configuration file (`~/.zshrc` or `~/.bashrc`) to make it permanent.

## Usage

Run the script by providing the path to your music folder:

```bash
python3 music.py /path/to/your/music/folder
```

### Main Menu Options

1.  **Process New Files**: Scans for untagged FLAC files and converts non-FLAC files. Recommended for new additions to your library.
2.  **Metadata Audit & Repair**: A deep scan of your entire library. Useful for fixing inconsistent naming or filling in gaps in your collection.
3.  **View Statistics**: Shows how much of your library is tagged, top composers, and disk usage.
4.  **Settings**: Change the AI model used for analysis (default: `google/gemini-3-flash-preview`).
5.  **Generate Cover Art**: Creates programmatic, geometric cover art for files without embedded images.

## Customizable Settings

You can change the default AI model in the **Settings** menu or by modifying the `DEFAULT_MODEL` variable in the script.

## Notes

-   **Backup**: The script creates backups of converted files in `~/Desktop/music_backups/` before replacing them.
-   **Safety**: "Dry Run" modes are available for most operations, allowing you to preview changes before applying them.

---

*Happy Listening! ♪ ♫*
