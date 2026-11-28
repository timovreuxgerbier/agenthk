# Shyft test: READ ME FIRST (Mac, kit 3)

Thank you for testing Shyft. It takes 30 to 90 minutes, mostly waiting.
It uses only made-up screenshots. Nothing of yours is read, and nothing leaves your Mac.

**You need:** a Mac with macOS 14 (Sonoma) or newer, at least 8 GB of memory (16 GB is better),
about 18 GB of free disk space, Wi-Fi, and the charger.

## 1. Double-click "1 Install Shyft"
A Terminal window opens and walks you through it. It installs Ollama (free) only if you
don't have it, and downloads Rick's and Zippy's models. This is the long part.
Anything already on your Mac stays as it is. If your Ollama is older than this version of
Shyft needs, the installer says so before downloading anything; update it from ollama.com.

**If your Mac says it "could not verify" the file:** that's because we're a student team, not a
registered Apple developer. Click **Done**, then open **System Settings > Privacy & Security**,
scroll down, click **Open Anyway** next to the file's name, and confirm. You do this once per file.

## 2. Double-click "2 Run the Shyft test"
Two runs on the made-up screenshots. It closes and restarts Ollama, with Ollama's cloud
turned off. Leave the window open; it can look frozen while it works.
Your Mac stays awake by itself until it's done.

## 3. Send the results
A folder called **Shyft test results** appears on your Desktop. Open `my_mac.txt`, type your
Mac's year (Apple menu > About This Mac), save, and send the whole folder to Sphinx.

Every run starts with a short notice called "WHERE YOUR FILES ARE", so `run_A.txt` and
`run_B.txt` include it. On a Mac it says "couldn't check" for now: those checks (OneDrive,
disk encryption) are written for Windows only so far. No folder paths and no names.

**If something breaks** (it stops, or your Mac struggles): that's a result, not a failure.
Send the folder anyway.

## 4. When you're done
Double-click **"3 Remove Shyft"**. It removes only what the kit brought: the models it downloaded
and the Shyft folder it made. It keeps your results folder, and tells you how to remove Ollama
if the kit installed it.
