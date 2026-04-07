# Google Image Translator Automation

A standalone utility designed to automate bulk image translations via Google Translate. By directly hooking into Chrome via CDP (Chrome DevTools Protocol), the app can concurrently process large batches of images, eliminating repetitive manual uploads.

## Prerequisites

- Windows OS
- Google Chrome installed on your system.

## Configuration & Setup

Since this is a portable executable, there is no installation required. However, you must absolutely ensure that **Google Chrome** is installed on your computer before proceeding.

1. **Verify Chrome Path**: By default, the application will attempt to launch Chrome from the standard directory: `C:\Program Files\Google\Chrome\Application\chrome.exe`. 
2. **Setup .env**:
   - Double-click the `setup_env.bat` file. This will automatically generate a `.env` configuration file for you.
   - (Optional) If you installed Chrome in a custom directory, you must configure the environment path:
     - Open the newly created `.env` file using Notepad (or any text editor).
     - Replace the `CHROME_PATH` existing value with the exact path to your `chrome.exe` and save the file.

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
