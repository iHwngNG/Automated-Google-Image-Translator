# Google Image Translator Automation

A standalone utility designed to automate bulk image translations via Google Translate. By directly hooking into Chrome via CDP (Chrome DevTools Protocol), the app can concurrently process large batches of images, eliminating repetitive manual uploads.

## Prerequisites

- Windows OS
- Google Chrome installed on your system.

## Configuration & Setup

Since this is a portable executable, there is no installation required. However, you need to ensure the app knows where to find Google Chrome.

1. Place `GoogleImageTranslator.exe` in your workspace.
2. By default, the app looks for Chrome at `C:\Program Files\Google\Chrome\Application\chrome.exe`. If you installed Chrome in a custom directory:
   - Make a copy of the provided `.env.example` file and rename it to `.env` (ensure it is in the same folder as the executable).
   - Open `.env` using any text editor and replace the `CHROME_PATH` value with the actual path to your `chrome.exe`.

## Walkthrough

1. Double-click `GoogleImageTranslator.exe` to launch the UI.
2. **Input Folder**: Click 'Browser...' to select the directory containing your images (.png, .jpg, .jpeg, .webp, .gif).
3. **Output Folder**: 
   - Manually assign an output directory.
   - Alternatively, check the auto-generation box to let the app create a structured output folder (nested inside an `outputs` directory) based on your input path.
4. **Languages**: Choose the original language of your images and the language you want them translated to.
5. **Concurrency**: Adjust the number of parallel tabs. It is recommended to keep this between 3 to 5 to prevent being rate-limited.
6. **Cleanup**: Optionally check the box to automatically delete the source images once they have been successfully processed. 
7. Hit **START TRANSLATION**. The application will launch an isolated browser session and process your queue automatically.
